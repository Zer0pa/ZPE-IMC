use unicode_normalization::UnicodeNormalization;
use wasm_bindgen::prelude::*;

const WORD_MASK: u32 = 0x000F_FFFF;
const MODE_SHIFT: u32 = 18;
const VERSION_SHIFT: u32 = 16;
const PAYLOAD_MASK: u32 = 0x0000_FFFF;
const MODE_NORMAL: u32 = 0;
const MODE_ESCAPE: u32 = 1;
const MODE_EXTENSION: u32 = 2;
const MODE_RESERVED: u32 = 3;
const DEFAULT_VERSION: u32 = 0;

fn flush_escape_buffer(escape: &mut Vec<u8>, out: &mut String) -> Result<(), JsValue> {
    if escape.is_empty() {
        return Ok(());
    }
    match String::from_utf8(std::mem::take(escape)) {
        Ok(chunk) => {
            out.push_str(&chunk);
            Ok(())
        }
        Err(_) => Err(JsValue::from_str("invalid UTF-8 bytes in escape buffer")),
    }
}

#[wasm_bindgen]
pub fn module_version() -> String {
    "0.1.0".to_string()
}

#[wasm_bindgen]
pub fn encode_text(text: &str) -> Vec<u32> {
    // Keep parity with Python-side normalization semantics.
    let normalized: String = text.nfd().collect();
    let bytes = normalized.as_bytes();
    let mut ids = Vec::with_capacity((bytes.len() + 1) / 2);

    for chunk in bytes.chunks(2) {
        let b0 = chunk[0] as u32;
        let b1 = if chunk.len() == 2 { chunk[1] as u32 } else { 0 };
        let word = (MODE_ESCAPE << MODE_SHIFT) | (b0 << 8) | b1;
        ids.push(word);
    }

    ids
}

#[wasm_bindgen]
pub fn decode_words(words: &[u32]) -> Result<String, JsValue> {
    let mut out = String::new();
    let mut escape_buf: Vec<u8> = Vec::new();

    for &word in words {
        if word > WORD_MASK {
            return Err(JsValue::from_str("word out of range"));
        }

        let mode = (word >> MODE_SHIFT) & 0x3;

        match mode {
            MODE_NORMAL => {
                flush_escape_buffer(&mut escape_buf, &mut out)?;

                let version = (word >> VERSION_SHIFT) & 0x3;
                if version != DEFAULT_VERSION {
                    return Err(JsValue::from_str("unsupported version in normal word"));
                }

                let codepoint = word & PAYLOAD_MASK;
                let ch = char::from_u32(codepoint)
                    .ok_or_else(|| JsValue::from_str("invalid Unicode codepoint"))?;
                out.push(ch);
            }
            MODE_ESCAPE => {
                let version = (word >> VERSION_SHIFT) & 0x3;
                if version != DEFAULT_VERSION {
                    return Err(JsValue::from_str("unsupported version in escape word"));
                }
                let b0 = ((word >> 8) & 0xFF) as u8;
                let b1 = (word & 0xFF) as u8;
                escape_buf.push(b0);
                if b1 != 0 {
                    escape_buf.push(b1);
                }
            }
            MODE_EXTENSION | MODE_RESERVED => {
                return Err(JsValue::from_str("unsupported extension word for wasm text codec"));
            }
            _ => {
                return Err(JsValue::from_str("unsupported mode"));
            }
        }
    }

    flush_escape_buffer(&mut escape_buf, &mut out)?;
    Ok(out.nfc().collect())
}
