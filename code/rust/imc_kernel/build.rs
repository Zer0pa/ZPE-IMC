use std::env;
use std::fs;
use std::fs::File;
use std::io::Write;
use std::path::PathBuf;

fn main() {
    let manifest_dir = PathBuf::from(env::var("CARGO_MANIFEST_DIR").expect("missing manifest dir"));
    let mapping_path = manifest_dir.join("../../zpe_multimodal/data/mapping_v1.json");
    println!("cargo:rerun-if-changed={}", mapping_path.display());

    let raw = fs::read_to_string(&mapping_path).expect("failed to read mapping_v1.json");
    let mut entries: Vec<(u32, u32)> =
        serde_json::from_str::<serde_json::Map<String, serde_json::Value>>(&raw)
            .expect("failed to parse mapping_v1.json")
            .into_iter()
            .map(|(codepoint, word)| {
                (
                    codepoint.parse::<u32>().expect("invalid codepoint key"),
                    word.as_u64().expect("word must be u64") as u32,
                )
            })
            .collect();
    entries.sort_unstable_by_key(|(codepoint, _)| *codepoint);

    let out_dir = PathBuf::from(env::var("OUT_DIR").expect("missing OUT_DIR"));
    let dest_path = out_dir.join("generated_text_map.rs");
    let mut file = File::create(&dest_path).expect("failed to create generated_text_map.rs");

    writeln!(
        &mut file,
        "static CHAR_TO_WORD: phf::Map<u32, u32> = phf::phf_map! {{"
    )
    .expect("failed to write text map header");
    for (codepoint, word) in entries {
        writeln!(&mut file, "    {codepoint}u32 => {word}u32,")
            .expect("failed to write text map entry");
    }
    writeln!(&mut file, "}};").expect("failed to write text map footer");
}
