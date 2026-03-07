use bumpalo::collections::Vec as BumpVec;
use bumpalo::Bump;
use mimalloc::MiMalloc;
use pyo3::exceptions::PyBufferError;
use pyo3::exceptions::PyRuntimeError;
use pyo3::exceptions::PyValueError;
use pyo3::ffi;
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyBool, PyDict, PyList, PyModule};
use rayon::prelude::*;
use std::os::raw::{c_char, c_int, c_void};
use std::ptr;
use std::sync::{OnceLock, RwLock};
use unicode_normalization::UnicodeNormalization;

const WORD_MASK: u32 = 0x000F_FFFF;
const PAYLOAD_16_MASK: u32 = 0x0000_FFFF;
const MODE_ESCAPE: u32 = 1;
const MODE_EXTENSION: u32 = 2;
const MODE_RESERVED: u32 = 3;

const TASTE_TYPE_BIT: u32 = 0x0400;
const MENTAL_TYPE_BIT: u32 = 0x0100;

const SEGMENT_MODALITIES: [&str; 8] = [
    "diagram", "music", "voice", "image", "mental", "touch", "smell", "taste",
];
const PAYLOAD_LAYOUT: &str = "u32le_bytes+spans_v1";
const FFI_CONTRACT_VERSION: &str = "imc_flat_u32le_v1";
const BUILD_PROFILE: &str = if cfg!(debug_assertions) {
    "debug"
} else {
    "release"
};

static NORMAL_WORDS: OnceLock<RwLock<Vec<u32>>> = OnceLock::new();

include!(concat!(env!("OUT_DIR"), "/generated_text_map.rs"));

#[global_allocator]
static GLOBAL: MiMalloc = MiMalloc;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum WordModality {
    Text,
    Diagram,
    Music,
    Voice,
    Image,
    Bpe,
    Mental,
    Touch,
    Smell,
    Taste,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum ChunkModality {
    Diagram,
    Music,
    Voice,
    Image,
    Mental,
    Touch,
    Smell,
    Taste,
}

#[derive(Clone, Copy)]
struct ImageMeta {
    width: u32,
    height: u32,
    root: u32,
    bit_depth: u8,
    threshold_x10: u32,
}

#[derive(Clone, Copy)]
enum ImageTask {
    Emit(u32),
    Visit { x: usize, y: usize, size: usize },
}

#[derive(Clone, Debug)]
struct StreamItem {
    word: Option<u32>,
    invalid_message: Option<String>,
}

#[derive(Default)]
struct SegmentBuffer {
    words: Vec<u32>,
    spans: Vec<u32>,
}

#[pyclass]
struct NativeBuffer {
    data: Vec<u32>,
    shape: [isize; 1],
    strides: [isize; 1],
    format: [c_char; 2],
}

impl SegmentBuffer {
    fn with_capacity(word_capacity: usize, span_capacity: usize) -> Self {
        Self {
            words: Vec::with_capacity(word_capacity),
            spans: Vec::with_capacity(span_capacity),
        }
    }
}

impl NativeBuffer {
    fn from_u32(data: Vec<u32>) -> Self {
        Self {
            shape: [data.len() as isize],
            strides: [std::mem::size_of::<u32>() as isize],
            format: [b'I' as c_char, 0],
            data,
        }
    }
}

#[pymethods]
impl NativeBuffer {
    unsafe fn __getbuffer__(
        slf: Bound<'_, Self>,
        view: *mut ffi::Py_buffer,
        flags: c_int,
    ) -> PyResult<()> {
        if view.is_null() {
            return Err(PyBufferError::new_err("View is null"));
        }
        if (flags & ffi::PyBUF_WRITABLE) == ffi::PyBUF_WRITABLE {
            return Err(PyBufferError::new_err("Object is not writable"));
        }

        let (buf, len, shape, strides, format) = {
            let borrowed = slf.borrow();
            (
                if borrowed.data.is_empty() {
                    ptr::null_mut()
                } else {
                    borrowed.data.as_ptr() as *mut c_void
                },
                (borrowed.data.len() * std::mem::size_of::<u32>()) as isize,
                borrowed.shape.as_ptr() as *mut isize,
                borrowed.strides.as_ptr() as *mut isize,
                borrowed.format.as_ptr() as *mut c_char,
            )
        };

        unsafe {
            (*view).obj = slf.into_any().into_ptr();
            (*view).buf = buf;
            (*view).len = len;
            (*view).readonly = 1;
            (*view).itemsize = std::mem::size_of::<u32>() as isize;
            (*view).format = if (flags & ffi::PyBUF_FORMAT) == ffi::PyBUF_FORMAT {
                format
            } else {
                ptr::null_mut()
            };
            (*view).ndim = 1;
            (*view).shape = if (flags & ffi::PyBUF_ND) == ffi::PyBUF_ND {
                shape
            } else {
                ptr::null_mut()
            };
            (*view).strides = if (flags & ffi::PyBUF_STRIDES) == ffi::PyBUF_STRIDES {
                strides
            } else {
                ptr::null_mut()
            };
            (*view).suboffsets = ptr::null_mut();
            (*view).internal = ptr::null_mut();
        }
        Ok(())
    }

    unsafe fn __releasebuffer__(&self, _view: *mut ffi::Py_buffer) {}
}

#[derive(Default)]
struct ScanState {
    counts: [usize; 10],
    text_words: Vec<u32>,
    validation_errors: Vec<String>,
    diagram_chunks: SegmentBuffer,
    music_chunks: SegmentBuffer,
    voice_chunks: SegmentBuffer,
    image_chunks: SegmentBuffer,
    mental_chunks: SegmentBuffer,
    touch_chunks: SegmentBuffer,
    smell_chunks: SegmentBuffer,
    taste_chunks: SegmentBuffer,
    current_type: Option<ChunkModality>,
    current_chunk_start: Option<usize>,
}

impl ScanState {
    fn with_word_capacity(word_count: usize) -> Self {
        let image_capacity = word_count.saturating_mul(5) / 8 + 8;
        let text_capacity = word_count / 10 + 8;
        let diagram_capacity = word_count / 8 + 8;
        let music_capacity = word_count / 16 + 8;
        let voice_capacity = word_count / 24 + 8;
        let mental_capacity = word_count / 24 + 8;
        let touch_capacity = word_count / 24 + 8;
        let smell_capacity = word_count / 32 + 8;
        let taste_capacity = word_count / 32 + 8;
        let span_capacity = |capacity: usize| capacity / 8 + 4;
        Self {
            text_words: Vec::with_capacity(text_capacity),
            validation_errors: Vec::new(),
            diagram_chunks: SegmentBuffer::with_capacity(
                diagram_capacity,
                span_capacity(diagram_capacity),
            ),
            music_chunks: SegmentBuffer::with_capacity(
                music_capacity,
                span_capacity(music_capacity),
            ),
            voice_chunks: SegmentBuffer::with_capacity(
                voice_capacity,
                span_capacity(voice_capacity),
            ),
            image_chunks: SegmentBuffer::with_capacity(
                image_capacity,
                span_capacity(image_capacity),
            ),
            mental_chunks: SegmentBuffer::with_capacity(
                mental_capacity,
                span_capacity(mental_capacity),
            ),
            touch_chunks: SegmentBuffer::with_capacity(
                touch_capacity,
                span_capacity(touch_capacity),
            ),
            smell_chunks: SegmentBuffer::with_capacity(
                smell_capacity,
                span_capacity(smell_capacity),
            ),
            taste_chunks: SegmentBuffer::with_capacity(
                taste_capacity,
                span_capacity(taste_capacity),
            ),
            ..Self::default()
        }
    }
}

fn modality_index(modality: WordModality) -> usize {
    match modality {
        WordModality::Text => 0,
        WordModality::Diagram => 1,
        WordModality::Music => 2,
        WordModality::Voice => 3,
        WordModality::Image => 4,
        WordModality::Bpe => 5,
        WordModality::Mental => 6,
        WordModality::Touch => 7,
        WordModality::Smell => 8,
        WordModality::Taste => 9,
    }
}

const fn classify_extension_payload(payload_hi: u8) -> WordModality {
    if (payload_hi & 0x40) != 0 {
        WordModality::Music
    } else if (payload_hi & 0x20) != 0 {
        WordModality::Voice
    } else if (payload_hi & 0x80) != 0 {
        WordModality::Diagram
    } else if (payload_hi & 0x10) != 0 {
        WordModality::Bpe
    } else {
        let is_image = (payload_hi & 0x0C) == 0x04;
        if (payload_hi & 0x08) != 0 && !is_image {
            WordModality::Touch
        } else if (payload_hi & 0x02) != 0 && !is_image {
            WordModality::Smell
        } else if (payload_hi & 0x01) != 0 && !is_image {
            WordModality::Mental
        } else if is_image {
            WordModality::Image
        } else {
            WordModality::Text
        }
    }
}

const fn build_classify_lut() -> [WordModality; 256] {
    let mut lut = [WordModality::Text; 256];
    let mut idx = 0usize;
    while idx < 256 {
        lut[idx] = classify_extension_payload(idx as u8);
        idx += 1;
    }
    lut
}

const CLASSIFY_LUT: [WordModality; 256] = build_classify_lut();

fn word_fields(word: u32) -> (u32, u32, u32) {
    let mode = (word >> 18) & 0x3;
    let version = (word >> 16) & 0x3;
    let payload = word & PAYLOAD_16_MASK;
    (mode, version, payload)
}

fn make_escape_word(byte0: u8, byte1: u8) -> u32 {
    (MODE_ESCAPE << 18) | ((byte0 as u32) << 8) | byte1 as u32
}

fn flush_escape_words(escape_bytes: &mut Vec<u8>, out: &mut Vec<u32>) {
    if escape_bytes.is_empty() {
        return;
    }
    out.reserve((escape_bytes.len() + 1) / 2);
    for chunk in escape_bytes.chunks(2) {
        let b0 = chunk[0];
        let b1 = *chunk.get(1).unwrap_or(&0);
        out.push(make_escape_word(b0, b1));
    }
    escape_bytes.clear();
}

fn encode_text_native(text: &str) -> Vec<u32> {
    let mut words = Vec::with_capacity(text.chars().count());
    let mut escape_bytes = Vec::with_capacity(8);

    for ch in text.nfd() {
        if let Some(&word) = CHAR_TO_WORD.get(&(ch as u32)) {
            flush_escape_words(&mut escape_bytes, &mut words);
            words.push(word);
            continue;
        }
        let mut utf8 = [0u8; 4];
        let encoded = ch.encode_utf8(&mut utf8);
        escape_bytes.extend_from_slice(encoded.as_bytes());
    }

    flush_escape_words(&mut escape_bytes, &mut words);
    words
}

const IMAGE_ENHANCED_FAMILY_VALUE: u32 = 0x0400;
const IMAGE_DATA_FLAG: u32 = 0x0200;
const IMAGE_CMD_TL: u32 = 0;
const IMAGE_CMD_TR: u32 = 1;
const IMAGE_CMD_BL: u32 = 2;
const IMAGE_CMD_BR: u32 = 3;
const IMAGE_CMD_PAINT: u32 = 4;
const IMAGE_CMD_SET_COLOR: u32 = 5;
const IMAGE_CMD_BACKTRACK: u32 = 6;
const IMAGE_CMD_META: u32 = 7;
const IMAGE_META_BEGIN: u32 = 0;
const IMAGE_META_END: u32 = 1;
const IMAGE_M_WIDTH_HI: u32 = 0;
const IMAGE_M_WIDTH_LO: u32 = 1;
const IMAGE_M_HEIGHT_HI: u32 = 2;
const IMAGE_M_HEIGHT_LO: u32 = 3;
const IMAGE_M_ROOT_HI: u32 = 4;
const IMAGE_M_ROOT_LO: u32 = 5;
const IMAGE_M_BIT_DEPTH: u32 = 6;
const IMAGE_M_THRESH_X10: u32 = 7;
const IMAGE_C_R: u32 = 0;
const IMAGE_C_G: u32 = 1;
const IMAGE_C_B: u32 = 2;
const IMAGE_MAX_RUN: u32 = 63;

fn round_ties_even_u32(value: f64) -> u32 {
    let floor = value.floor();
    let frac = value - floor;
    if frac < 0.5 {
        floor as u32
    } else if frac > 0.5 {
        floor as u32 + 1
    } else if (floor as u64) % 2 == 0 {
        floor as u32
    } else {
        floor as u32 + 1
    }
}

fn next_pow2(mut value: usize) -> usize {
    if value <= 1 {
        return 1;
    }
    value -= 1;
    value |= value >> 1;
    value |= value >> 2;
    value |= value >> 4;
    value |= value >> 8;
    value |= value >> 16;
    if usize::BITS > 32 {
        value |= value >> 32;
    }
    value + 1
}

fn image_ext_word(payload: u32) -> u32 {
    (MODE_EXTENSION << 18) | (payload & 0xFFFF)
}

fn image_cmd_word(cmd: u32, arg: u32) -> u32 {
    let run = arg.min(IMAGE_MAX_RUN);
    let payload = IMAGE_ENHANCED_FAMILY_VALUE | ((cmd & 0x7) << 6) | (run & 0x3F);
    image_ext_word(payload)
}

fn image_data_word(kind: u32, value: u32) -> u32 {
    let payload =
        IMAGE_ENHANCED_FAMILY_VALUE | IMAGE_DATA_FLAG | ((kind & 0x7) << 6) | (value & 0x3F);
    image_ext_word(payload)
}

fn image_pack_u12(value: u32) -> (u32, u32) {
    let clamped = value.min(0xFFF);
    ((clamped >> 6) & 0x3F, clamped & 0x3F)
}

fn quantize_level(value: u8, maxq: u32) -> u8 {
    if maxq == 0 {
        return 0;
    }
    round_ties_even_u32((value as f64 / 255.0) * maxq as f64) as u8
}

fn dequantize_level(level: u8, maxq: u32) -> u8 {
    if maxq == 0 {
        return 0;
    }
    round_ties_even_u32((level as f64 / maxq as f64) * 255.0) as u8
}

struct ImagePrefixStats {
    stride: usize,
    sum_r: Vec<u64>,
    sum_g: Vec<u64>,
    sum_b: Vec<u64>,
    sq_r: Vec<u64>,
    sq_g: Vec<u64>,
    sq_b: Vec<u64>,
}

impl ImagePrefixStats {
    fn build(padded: &[u8], root: usize) -> Self {
        let stride = root + 1;
        let len = stride * stride;
        let mut sum_r = vec![0u64; len];
        let mut sum_g = vec![0u64; len];
        let mut sum_b = vec![0u64; len];
        let mut sq_r = vec![0u64; len];
        let mut sq_g = vec![0u64; len];
        let mut sq_b = vec![0u64; len];

        for y in 0..root {
            let mut row_r = 0u64;
            let mut row_g = 0u64;
            let mut row_b = 0u64;
            let mut row_sq_r = 0u64;
            let mut row_sq_g = 0u64;
            let mut row_sq_b = 0u64;
            for x in 0..root {
                let src = (y * root + x) * 3;
                let r = padded[src] as u64;
                let g = padded[src + 1] as u64;
                let b = padded[src + 2] as u64;
                row_r += r;
                row_g += g;
                row_b += b;
                row_sq_r += r * r;
                row_sq_g += g * g;
                row_sq_b += b * b;

                let idx = (y + 1) * stride + (x + 1);
                let up = y * stride + (x + 1);
                sum_r[idx] = sum_r[up] + row_r;
                sum_g[idx] = sum_g[up] + row_g;
                sum_b[idx] = sum_b[up] + row_b;
                sq_r[idx] = sq_r[up] + row_sq_r;
                sq_g[idx] = sq_g[up] + row_sq_g;
                sq_b[idx] = sq_b[up] + row_sq_b;
            }
        }

        Self {
            stride,
            sum_r,
            sum_g,
            sum_b,
            sq_r,
            sq_g,
            sq_b,
        }
    }

    fn region_total(table: &[u64], stride: usize, x: usize, y: usize, size: usize) -> u64 {
        let x2 = x + size;
        let y2 = y + size;
        table[y2 * stride + x2] - table[y * stride + x2] - table[y2 * stride + x]
            + table[y * stride + x]
    }

    fn region_stats(&self, x: usize, y: usize, size: usize) -> (f64, (u8, u8, u8)) {
        let count = (size * size) as f64;
        let sum_r = Self::region_total(&self.sum_r, self.stride, x, y, size) as f64;
        let sum_g = Self::region_total(&self.sum_g, self.stride, x, y, size) as f64;
        let sum_b = Self::region_total(&self.sum_b, self.stride, x, y, size) as f64;
        let sq_r = Self::region_total(&self.sq_r, self.stride, x, y, size) as f64;
        let sq_g = Self::region_total(&self.sq_g, self.stride, x, y, size) as f64;
        let sq_b = Self::region_total(&self.sq_b, self.stride, x, y, size) as f64;

        let mean_r = sum_r / count;
        let mean_g = sum_g / count;
        let mean_b = sum_b / count;
        let var_r = (sq_r / count) - (mean_r * mean_r);
        let var_g = (sq_g / count) - (mean_g * mean_g);
        let var_b = (sq_b / count) - (mean_b * mean_b);

        (
            (var_r + var_g + var_b) / 3.0,
            (
                round_ties_even_u32(mean_r) as u8,
                round_ties_even_u32(mean_g) as u8,
                round_ties_even_u32(mean_b) as u8,
            ),
        )
    }
}

fn emit_color_words(
    words: &mut Vec<u32>,
    current: &mut (i32, i32, i32),
    mean_rgb: (u8, u8, u8),
    maxq: u32,
) {
    let levels = (
        quantize_level(mean_rgb.0, maxq) as i32,
        quantize_level(mean_rgb.1, maxq) as i32,
        quantize_level(mean_rgb.2, maxq) as i32,
    );
    if levels == *current {
        return;
    }
    words.push(image_cmd_word(IMAGE_CMD_SET_COLOR, 1));
    words.push(image_data_word(IMAGE_C_R, levels.0 as u32));
    words.push(image_data_word(IMAGE_C_G, levels.1 as u32));
    words.push(image_data_word(IMAGE_C_B, levels.2 as u32));
    *current = levels;
}

fn encode_quadtree_native(
    image_data: &[u8],
    width: u32,
    height: u32,
    bit_depth: u8,
    threshold: f32,
) -> PyResult<(Vec<u32>, ImageMeta)> {
    if !(1..=6).contains(&bit_depth) {
        return Err(PyValueError::new_err("bit_depth supported range is [1,6]"));
    }
    let width_usize = width as usize;
    let height_usize = height as usize;
    let expected_len = width_usize
        .checked_mul(height_usize)
        .and_then(|pixels| pixels.checked_mul(3))
        .ok_or_else(|| PyValueError::new_err("image dimensions overflow"))?;
    if image_data.len() != expected_len {
        return Err(PyValueError::new_err(
            "image data length does not match width*height*3",
        ));
    }

    let root = next_pow2(width_usize.max(height_usize));
    let threshold_x10 = round_ties_even_u32(f64::from(threshold) * 10.0);
    let meta = ImageMeta {
        width,
        height,
        root: root as u32,
        bit_depth,
        threshold_x10,
    };

    let maxq = ((1u32 << bit_depth) - 1).max(1);
    let dequant_lut: Vec<u8> = (0..=maxq)
        .map(|level| dequantize_level(level as u8, maxq))
        .collect();
    let arena = Bump::with_capacity(root * root * 3 + 4096);
    let mut padded = BumpVec::with_capacity_in(root * root * 3, &arena);
    padded.resize(root * root * 3, 0u8);

    for y in 0..height_usize {
        for x in 0..width_usize {
            let src = (y * width_usize + x) * 3;
            let dst = (y * root + x) * 3;
            let r_level = quantize_level(image_data[src], maxq);
            let g_level = quantize_level(image_data[src + 1], maxq);
            let b_level = quantize_level(image_data[src + 2], maxq);
            padded[dst] = dequant_lut[r_level as usize];
            padded[dst + 1] = dequant_lut[g_level as usize];
            padded[dst + 2] = dequant_lut[b_level as usize];
        }
    }

    let stats = ImagePrefixStats::build(&padded, root);
    let mut words = Vec::with_capacity(root * root / 2 + 32);
    words.push(image_cmd_word(IMAGE_CMD_META, IMAGE_META_BEGIN));
    let (w_hi, w_lo) = image_pack_u12(width);
    let (h_hi, h_lo) = image_pack_u12(height);
    let (r_hi, r_lo) = image_pack_u12(root as u32);
    words.extend_from_slice(&[
        image_data_word(IMAGE_M_WIDTH_HI, w_hi),
        image_data_word(IMAGE_M_WIDTH_LO, w_lo),
        image_data_word(IMAGE_M_HEIGHT_HI, h_hi),
        image_data_word(IMAGE_M_HEIGHT_LO, h_lo),
        image_data_word(IMAGE_M_ROOT_HI, r_hi),
        image_data_word(IMAGE_M_ROOT_LO, r_lo),
        image_data_word(IMAGE_M_BIT_DEPTH, bit_depth as u32),
        image_data_word(IMAGE_M_THRESH_X10, threshold_x10),
    ]);
    words.push(image_cmd_word(IMAGE_CMD_META, IMAGE_META_END));

    let mut current = (-1, -1, -1);
    let mut tasks = BumpVec::with_capacity_in(root * 2, &arena);
    tasks.push(ImageTask::Visit {
        x: 0,
        y: 0,
        size: root,
    });

    while let Some(task) = tasks.pop() {
        match task {
            ImageTask::Emit(word) => words.push(word),
            ImageTask::Visit { x, y, size } => {
                let (variance, mean_rgb) = stats.region_stats(x, y, size);
                if size == 1 || variance <= f64::from(threshold) {
                    emit_color_words(&mut words, &mut current, mean_rgb, maxq);
                    words.push(image_cmd_word(IMAGE_CMD_PAINT, 1));
                    continue;
                }

                let half = size / 2;
                for (cmd, nx, ny) in [
                    (IMAGE_CMD_BR, x + half, y + half),
                    (IMAGE_CMD_BL, x, y + half),
                    (IMAGE_CMD_TR, x + half, y),
                    (IMAGE_CMD_TL, x, y),
                ] {
                    tasks.push(ImageTask::Emit(image_cmd_word(IMAGE_CMD_BACKTRACK, 1)));
                    tasks.push(ImageTask::Visit {
                        x: nx,
                        y: ny,
                        size: half,
                    });
                    tasks.push(ImageTask::Emit(image_cmd_word(cmd, 1)));
                }
            }
        }
    }

    Ok((words, meta))
}

fn image_payload(word: u32) -> Option<u32> {
    let (mode, version, payload) = word_fields(word);
    if mode == MODE_EXTENSION
        && version == 0
        && (payload & 0x0C00) == IMAGE_ENHANCED_FAMILY_VALUE
    {
        Some(payload)
    } else {
        None
    }
}

fn image_dequant_lut(bit_depth: u8) -> Vec<u8> {
    let maxq = ((1u32 << bit_depth) - 1).max(1);
    (0..=maxq)
        .map(|level| dequantize_level(level as u8, maxq))
        .collect()
}

fn paint_region_rgb(
    canvas: &mut [u8],
    width: usize,
    height: usize,
    x: usize,
    y: usize,
    size: usize,
    rgb: (u8, u8, u8),
) {
    if x >= width || y >= height {
        return;
    }
    let x_end = (x + size).min(width);
    let y_end = (y + size).min(height);
    for row in y..y_end {
        let row_start = (row * width + x) * 3;
        let row_slice = &mut canvas[row_start..row_start + (x_end - x) * 3];
        for pixel in row_slice.chunks_exact_mut(3) {
            pixel[0] = rgb.0;
            pixel[1] = rgb.1;
            pixel[2] = rgb.2;
        }
    }
}

fn decode_quadtree_native(words: &[u32]) -> PyResult<(Vec<u8>, ImageMeta)> {
    let mut meta_open = false;
    let mut meta_vals = [0u32; 8];
    let mut required_meta = [false; 8];
    let mut meta_begin_count = 0usize;
    let mut meta_end_count = 0usize;
    let mut meta: Option<ImageMeta> = None;
    let mut canvas: Vec<u8> = Vec::new();
    let mut stack: Vec<(usize, usize, usize)> = Vec::new();
    let mut pending_channels = [0u32; 3];
    let mut seen_channels = [false; 3];
    let mut expecting_color = false;
    let mut current = (0u8, 0u8, 0u8);
    let mut dequant_lut: Vec<u8> = Vec::new();
    let mut saw_set_color = false;
    let mut saw_paint = false;

    for &word in words {
        let Some(payload) = image_payload(word) else {
            continue;
        };

        if (payload & IMAGE_DATA_FLAG) != 0 {
            let kind = ((payload >> 6) & 0x7) as usize;
            let value = payload & 0x3F;
            if meta_open {
                if kind >= meta_vals.len() {
                    return Err(PyValueError::new_err(
                        "invalid enhanced stream: metadata kind out of range",
                    ));
                }
                meta_vals[kind] = value;
                required_meta[kind] = true;
                continue;
            }
            if !expecting_color {
                return Err(PyValueError::new_err(
                    "invalid enhanced stream: unexpected data payload",
                ));
            }
            if kind > IMAGE_C_B as usize {
                return Err(PyValueError::new_err(
                    "invalid enhanced stream: non-color data outside metadata block",
                ));
            }
            if seen_channels[kind] {
                return Err(PyValueError::new_err(
                    "invalid enhanced stream: duplicate color channel payload",
                ));
            }
            seen_channels[kind] = true;
            pending_channels[kind] = value;
            if seen_channels.iter().all(|seen| *seen) {
                if dequant_lut.is_empty() {
                    return Err(PyValueError::new_err(
                        "invalid enhanced stream: metadata not initialized before color payload",
                    ));
                }
                current = (
                    dequant_lut[pending_channels[IMAGE_C_R as usize] as usize],
                    dequant_lut[pending_channels[IMAGE_C_G as usize] as usize],
                    dequant_lut[pending_channels[IMAGE_C_B as usize] as usize],
                );
                expecting_color = false;
            }
            continue;
        }

        let cmd = (payload >> 6) & 0x7;
        let arg = payload & 0x3F;
        let run = arg.max(1);

        if cmd == IMAGE_CMD_META {
            if arg == IMAGE_META_BEGIN {
                if meta_open {
                    return Err(PyValueError::new_err(
                        "invalid enhanced stream: nested META_BEGIN",
                    ));
                }
                if meta.is_some() {
                    return Err(PyValueError::new_err(
                        "invalid enhanced stream: duplicate metadata block",
                    ));
                }
                meta_open = true;
                meta_begin_count += 1;
                continue;
            }
            if arg == IMAGE_META_END {
                if !meta_open {
                    return Err(PyValueError::new_err(
                        "invalid enhanced stream: META_END without META_BEGIN",
                    ));
                }
                meta_open = false;
                meta_end_count += 1;

                if !required_meta.iter().all(|present| *present) {
                    return Err(PyValueError::new_err(
                        "invalid enhanced stream: missing required metadata fields",
                    ));
                }

                let width = ((meta_vals[IMAGE_M_WIDTH_HI as usize] & 0x3F) << 6)
                    | (meta_vals[IMAGE_M_WIDTH_LO as usize] & 0x3F);
                let height = ((meta_vals[IMAGE_M_HEIGHT_HI as usize] & 0x3F) << 6)
                    | (meta_vals[IMAGE_M_HEIGHT_LO as usize] & 0x3F);
                let root = ((meta_vals[IMAGE_M_ROOT_HI as usize] & 0x3F) << 6)
                    | (meta_vals[IMAGE_M_ROOT_LO as usize] & 0x3F);
                if root == 0 {
                    return Err(PyValueError::new_err(
                        "invalid enhanced stream: invalid root in metadata",
                    ));
                }
                let bit_depth = meta_vals[IMAGE_M_BIT_DEPTH as usize].clamp(1, 6) as u8;
                let threshold_x10 = meta_vals[IMAGE_M_THRESH_X10 as usize];
                let parsed_meta = ImageMeta {
                    width,
                    height,
                    root,
                    bit_depth,
                    threshold_x10,
                };
                let width_usize = width as usize;
                let height_usize = height as usize;
                canvas = vec![0u8; width_usize.saturating_mul(height_usize).saturating_mul(3)];
                stack.clear();
                stack.push((0, 0, root as usize));
                dequant_lut = image_dequant_lut(bit_depth);
                meta = Some(parsed_meta);
                continue;
            }
            return Err(PyValueError::new_err(
                "invalid enhanced stream: invalid META command arg",
            ));
        }

        if meta_open {
            return Err(PyValueError::new_err(
                "invalid enhanced stream: enhanced command encountered while metadata block is open",
            ));
        }

        let Some(meta_value) = meta else {
            return Err(PyValueError::new_err(
                "invalid enhanced stream: image commands appeared before metadata was complete",
            ));
        };

        match cmd {
            IMAGE_CMD_TL | IMAGE_CMD_TR | IMAGE_CMD_BL | IMAGE_CMD_BR => {
                for _ in 0..run {
                    let Some(&(x, y, size)) = stack.last() else {
                        return Err(PyValueError::new_err(
                            "invalid enhanced stream: missing traversal root",
                        ));
                    };
                    let half = (size / 2).max(1);
                    match cmd {
                        IMAGE_CMD_TL => stack.push((x, y, half)),
                        IMAGE_CMD_TR => stack.push((x + half, y, half)),
                        IMAGE_CMD_BL => stack.push((x, y + half, half)),
                        IMAGE_CMD_BR => stack.push((x + half, y + half, half)),
                        _ => unreachable!(),
                    }
                }
            }
            IMAGE_CMD_BACKTRACK => {
                for _ in 0..run {
                    if stack.len() <= 1 {
                        return Err(PyValueError::new_err(
                            "invalid enhanced stream: backtrack underflow",
                        ));
                    }
                    stack.pop();
                }
            }
            IMAGE_CMD_SET_COLOR => {
                if expecting_color {
                    return Err(PyValueError::new_err(
                        "invalid enhanced stream: incomplete prior color triplet",
                    ));
                }
                expecting_color = true;
                seen_channels = [false; 3];
                pending_channels = [0; 3];
                saw_set_color = true;
            }
            IMAGE_CMD_PAINT => {
                saw_paint = true;
                let Some(&(x, y, size)) = stack.last() else {
                    return Err(PyValueError::new_err(
                        "invalid enhanced stream: missing traversal root",
                    ));
                };
                paint_region_rgb(
                    &mut canvas,
                    meta_value.width as usize,
                    meta_value.height as usize,
                    x,
                    y,
                    size,
                    current,
                );
            }
            _ => {
                return Err(PyValueError::new_err(
                    "invalid enhanced stream: unknown command",
                ));
            }
        }
    }

    if meta_open {
        return Err(PyValueError::new_err(
            "invalid enhanced stream: ended with open metadata block",
        ));
    }
    if expecting_color {
        return Err(PyValueError::new_err(
            "invalid enhanced stream: ended with incomplete color triplet",
        ));
    }
    if meta_begin_count != 1 || meta_end_count != 1 {
        return Err(PyValueError::new_err(
            "invalid enhanced stream: metadata framing count invalid",
        ));
    }
    if stack.len() != 1 {
        return Err(PyValueError::new_err(
            "invalid enhanced stream: ended with unbalanced traversal depth",
        ));
    }
    if !saw_set_color || !saw_paint {
        return Err(PyValueError::new_err(
            "invalid enhanced stream: missing required SET_COLOR/PAINT sequence",
        ));
    }

    let Some(meta_value) = meta else {
        return Err(PyValueError::new_err(
            "invalid enhanced stream: metadata block missing",
        ));
    };
    Ok((canvas, meta_value))
}

fn classify_word(word: u32) -> WordModality {
    let (mode, _version, payload) = word_fields(word);
    if mode == MODE_RESERVED && (payload & MENTAL_TYPE_BIT) != 0 {
        return WordModality::Mental;
    }
    if mode != MODE_EXTENSION {
        return WordModality::Text;
    }
    CLASSIFY_LUT[(payload >> 8) as usize]
}

fn taste_sequence_length(items: &[StreamItem], start: usize) -> usize {
    if start + 2 >= items.len() {
        return 0;
    }

    let w0 = match items[start].word {
        Some(word) => word,
        None => return 0,
    };
    let w1 = match items[start + 1].word {
        Some(word) => word,
        None => return 0,
    };
    let w2 = match items[start + 2].word {
        Some(word) => word,
        None => return 0,
    };

    let (m0, v0, p0) = word_fields(w0);
    let (m1, v1, p1) = word_fields(w1);
    let (m2, v2, p2) = word_fields(w2);
    if m0 != MODE_EXTENSION
        || v0 != 0
        || (p0 & TASTE_TYPE_BIT) == 0
        || m1 != MODE_EXTENSION
        || v1 != 1
        || (p1 & TASTE_TYPE_BIT) == 0
        || m2 != MODE_EXTENSION
        || v2 != 2
        || (p2 & TASTE_TYPE_BIT) == 0
    {
        return 0;
    }

    let mut index = start + 3;
    while index < items.len() {
        let word = match items[index].word {
            Some(word) => word,
            None => break,
        };
        let (mode, version, payload) = word_fields(word);
        if mode == MODE_EXTENSION
            && (payload & TASTE_TYPE_BIT) != 0
            && (version == 2 || version == 3)
        {
            index += 1;
            continue;
        }
        break;
    }
    index - start
}

fn taste_sequence_length_words(words: &[u32], start: usize) -> usize {
    if start + 2 >= words.len() {
        return 0;
    }

    let w0 = words[start];
    let w1 = words[start + 1];
    let w2 = words[start + 2];
    if w0 > WORD_MASK || w1 > WORD_MASK || w2 > WORD_MASK {
        return 0;
    }

    let (m0, v0, p0) = word_fields(w0);
    let (m1, v1, p1) = word_fields(w1);
    let (m2, v2, p2) = word_fields(w2);
    if m0 != MODE_EXTENSION
        || v0 != 0
        || (p0 & TASTE_TYPE_BIT) == 0
        || m1 != MODE_EXTENSION
        || v1 != 1
        || (p1 & TASTE_TYPE_BIT) == 0
        || m2 != MODE_EXTENSION
        || v2 != 2
        || (p2 & TASTE_TYPE_BIT) == 0
    {
        return 0;
    }

    let mut index = start + 3;
    while index < words.len() {
        let word = words[index];
        if word > WORD_MASK {
            break;
        }
        let (mode, version, payload) = word_fields(word);
        if mode == MODE_EXTENSION
            && (payload & TASTE_TYPE_BIT) != 0
            && (version == 2 || version == 3)
        {
            index += 1;
            continue;
        }
        break;
    }
    index - start
}

fn type_name(obj: &Bound<'_, PyAny>) -> String {
    match obj.get_type().name() {
        Ok(name) => name.to_string(),
        Err(_) => "unknown".to_string(),
    }
}

fn inspect_word(index: usize, obj: &Bound<'_, PyAny>) -> StreamItem {
    if obj.is_instance_of::<PyBool>() {
        let word = if obj.is_truthy().unwrap_or(false) {
            1
        } else {
            0
        };
        return StreamItem {
            word: Some(word),
            invalid_message: None,
        };
    }

    let is_exact_int = unsafe { ffi::PyLong_CheckExact(obj.as_ptr()) == 1 };
    if !is_exact_int {
        return StreamItem {
            word: None,
            invalid_message: Some(format!(
                "index {index}: non-int word type={}",
                type_name(obj)
            )),
        };
    }

    match obj.extract::<i64>() {
        Ok(value) if (0..=WORD_MASK as i64).contains(&value) => StreamItem {
            word: Some(value as u32),
            invalid_message: None,
        },
        Ok(value) => StreamItem {
            word: None,
            invalid_message: Some(format!("index {index}: word out of range {value}")),
        },
        Err(_) => StreamItem {
            word: None,
            invalid_message: Some(format!("index {index}: word out of range int")),
        },
    }
}

fn collect_items(stream: &Bound<'_, PyAny>) -> PyResult<Vec<StreamItem>> {
    let mut items = Vec::new();
    for (index, item) in stream.try_iter()?.enumerate() {
        items.push(inspect_word(index, &item?));
    }
    Ok(items)
}

fn try_collect_fast_words(stream: &Bound<'_, PyAny>) -> PyResult<Option<Vec<u32>>> {
    Ok(stream.extract::<Vec<u32>>().ok())
}

impl ScanState {
    fn bump(&mut self, modality: WordModality) {
        self.counts[modality_index(modality)] += 1;
    }

    fn buffer_mut(&mut self, modality: ChunkModality) -> &mut SegmentBuffer {
        match modality {
            ChunkModality::Diagram => &mut self.diagram_chunks,
            ChunkModality::Music => &mut self.music_chunks,
            ChunkModality::Voice => &mut self.voice_chunks,
            ChunkModality::Image => &mut self.image_chunks,
            ChunkModality::Mental => &mut self.mental_chunks,
            ChunkModality::Touch => &mut self.touch_chunks,
            ChunkModality::Smell => &mut self.smell_chunks,
            ChunkModality::Taste => &mut self.taste_chunks,
        }
    }

    fn flush_current_chunk(&mut self) {
        let Some(modality) = self.current_type.take() else {
            self.current_chunk_start = None;
            return;
        };
        let Some(start) = self.current_chunk_start.take() else {
            return;
        };
        let buffer = self.buffer_mut(modality);
        let len = buffer.words.len().saturating_sub(start);
        if len > 0 {
            buffer.spans.push(start as u32);
            buffer.spans.push(len as u32);
        }
    }

    fn push_text_word(&mut self, modality: WordModality, word: u32) {
        self.flush_current_chunk();
        self.bump(modality);
        self.text_words.push(word);
    }

    fn push_chunk_word(
        &mut self,
        chunk_modality: ChunkModality,
        counted_as: WordModality,
        word: u32,
    ) {
        self.bump(counted_as);
        if self.current_type != Some(chunk_modality) {
            self.flush_current_chunk();
            self.current_type = Some(chunk_modality);
            let start = self.buffer_mut(chunk_modality).words.len();
            self.current_chunk_start = Some(start);
        }
        self.buffer_mut(chunk_modality).words.push(word);
    }
}

fn run_scan(items: &[StreamItem], record_invalid: bool) -> ScanState {
    let mut state = ScanState::default();
    let mut index = 0usize;

    while index < items.len() {
        let item = &items[index];
        let Some(word) = item.word else {
            state.flush_current_chunk();
            if record_invalid {
                if let Some(message) = &item.invalid_message {
                    state.validation_errors.push(message.clone());
                }
            }
            index += 1;
            continue;
        };

        let taste_len = taste_sequence_length(items, index);
        if taste_len > 0 {
            for offset in 0..taste_len {
                let taste_word = items[index + offset]
                    .word
                    .expect("taste sequence words are valid");
                state.push_chunk_word(ChunkModality::Taste, WordModality::Taste, taste_word);
            }
            index += taste_len;
            continue;
        }

        match classify_word(word) {
            WordModality::Text => state.push_text_word(WordModality::Text, word),
            WordModality::Bpe => state.push_text_word(WordModality::Bpe, word),
            WordModality::Diagram => {
                state.push_chunk_word(ChunkModality::Diagram, WordModality::Diagram, word)
            }
            WordModality::Music => {
                state.push_chunk_word(ChunkModality::Music, WordModality::Music, word)
            }
            WordModality::Voice => {
                state.push_chunk_word(ChunkModality::Voice, WordModality::Voice, word)
            }
            WordModality::Image => {
                state.push_chunk_word(ChunkModality::Image, WordModality::Image, word)
            }
            WordModality::Mental => {
                state.push_chunk_word(ChunkModality::Mental, WordModality::Mental, word)
            }
            WordModality::Touch => {
                state.push_chunk_word(ChunkModality::Touch, WordModality::Touch, word)
            }
            WordModality::Smell => {
                state.push_chunk_word(ChunkModality::Smell, WordModality::Smell, word)
            }
            WordModality::Taste => {
                state.push_chunk_word(ChunkModality::Taste, WordModality::Taste, word)
            }
        }
        index += 1;
    }

    state.flush_current_chunk();
    state
}

fn run_scan_words(words: &[u32], record_invalid: bool) -> ScanState {
    let mut state = ScanState::with_word_capacity(words.len());
    let mut index = 0usize;

    while index < words.len() {
        let word = words[index];
        if word > WORD_MASK {
            state.flush_current_chunk();
            if record_invalid {
                state
                    .validation_errors
                    .push(format!("index {index}: word out of range {word}"));
            }
            index += 1;
            continue;
        }

        let taste_len = taste_sequence_length_words(words, index);
        if taste_len > 0 {
            for &taste_word in &words[index..index + taste_len] {
                state.push_chunk_word(ChunkModality::Taste, WordModality::Taste, taste_word);
            }
            index += taste_len;
            continue;
        }

        match classify_word(word) {
            WordModality::Text => state.push_text_word(WordModality::Text, word),
            WordModality::Bpe => state.push_text_word(WordModality::Bpe, word),
            WordModality::Diagram => {
                state.push_chunk_word(ChunkModality::Diagram, WordModality::Diagram, word)
            }
            WordModality::Music => {
                state.push_chunk_word(ChunkModality::Music, WordModality::Music, word)
            }
            WordModality::Voice => {
                state.push_chunk_word(ChunkModality::Voice, WordModality::Voice, word)
            }
            WordModality::Image => {
                state.push_chunk_word(ChunkModality::Image, WordModality::Image, word)
            }
            WordModality::Mental => {
                state.push_chunk_word(ChunkModality::Mental, WordModality::Mental, word)
            }
            WordModality::Touch => {
                state.push_chunk_word(ChunkModality::Touch, WordModality::Touch, word)
            }
            WordModality::Smell => {
                state.push_chunk_word(ChunkModality::Smell, WordModality::Smell, word)
            }
            WordModality::Taste => {
                state.push_chunk_word(ChunkModality::Taste, WordModality::Taste, word)
            }
        }
        index += 1;
    }

    state.flush_current_chunk();
    state
}

fn set_segment_payload<'py>(
    py: Python<'py>,
    out: &Bound<'py, PyDict>,
    name: &str,
    buffer: SegmentBuffer,
) -> PyResult<()> {
    out.set_item(
        format!("{name}_words_u32le"),
        Py::new(py, NativeBuffer::from_u32(buffer.words))?,
    )?;
    out.set_item(
        format!("{name}_spans_u32le"),
        Py::new(py, NativeBuffer::from_u32(buffer.spans))?,
    )?;
    Ok(())
}

fn scan_state_to_py(py: Python<'_>, state: ScanState) -> PyResult<Py<PyDict>> {
    let ScanState {
        counts: counts_values,
        text_words,
        validation_errors: validation_errors_values,
        diagram_chunks,
        music_chunks,
        voice_chunks,
        image_chunks,
        mental_chunks,
        touch_chunks,
        smell_chunks,
        taste_chunks,
        ..
    } = state;

    let out = PyDict::new(py);
    let counts = PyList::empty(py);
    for count in counts_values {
        counts.append(count)?;
    }

    let validation_errors = PyList::empty(py);
    for error in &validation_errors_values {
        validation_errors.append(error)?;
    }

    out.set_item(
        "text_words_u32le",
        Py::new(py, NativeBuffer::from_u32(text_words))?,
    )?;
    out.set_item("counts", counts)?;
    set_segment_payload(py, &out, "diagram", diagram_chunks)?;
    set_segment_payload(py, &out, "music", music_chunks)?;
    set_segment_payload(py, &out, "voice", voice_chunks)?;
    set_segment_payload(py, &out, "image", image_chunks)?;
    set_segment_payload(py, &out, "mental", mental_chunks)?;
    set_segment_payload(py, &out, "touch", touch_chunks)?;
    set_segment_payload(py, &out, "smell", smell_chunks)?;
    set_segment_payload(py, &out, "taste", taste_chunks)?;
    out.set_item("segment_modalities", SEGMENT_MODALITIES)?;
    out.set_item("validation_errors", validation_errors)?;
    out.set_item("native_backend", true)?;
    out.set_item("backend", "rust")?;
    out.set_item("origin", "pyo3_native_extension")?;
    out.set_item("fallback_used", false)?;
    out.set_item("payload_layout", PAYLOAD_LAYOUT)?;
    out.set_item("ffi_contract_version", FFI_CONTRACT_VERSION)?;
    out.set_item("build_profile", BUILD_PROFILE)?;
    Ok(out.unbind())
}

#[pyfunction]
fn configure_normal_words(words: Vec<u32>) -> PyResult<usize> {
    let lock = NORMAL_WORDS.get_or_init(|| RwLock::new(Vec::new()));
    let mut guard = lock
        .write()
        .map_err(|_| PyRuntimeError::new_err("normal-word registry poisoned"))?;
    guard.clear();
    guard.extend(words);
    guard.sort_unstable();
    guard.dedup();
    Ok(guard.len())
}

#[pyfunction]
fn backend_info(py: Python<'_>) -> PyResult<Py<PyDict>> {
    let info = PyDict::new(py);
    let normal_word_count = NORMAL_WORDS
        .get()
        .and_then(|lock| lock.read().ok().map(|guard| guard.len()))
        .unwrap_or(0usize);
    info.set_item("backend", "rust")?;
    info.set_item("origin", "pyo3_native_extension")?;
    info.set_item("native", true)?;
    info.set_item("fallback_used", false)?;
    info.set_item("module_name", "zpe_imc_kernel")?;
    info.set_item("module_version", env!("CARGO_PKG_VERSION"))?;
    info.set_item("normal_word_count", normal_word_count)?;
    info.set_item("word_mask", WORD_MASK)?;
    info.set_item("payload_layout", PAYLOAD_LAYOUT)?;
    info.set_item("ffi_contract_version", FFI_CONTRACT_VERSION)?;
    info.set_item("normal_word_registry_kind", "sorted_vec")?;
    info.set_item("allocator", "mimalloc")?;
    info.set_item("scan_fast_path", "u32_sequence_extract_v1")?;
    info.set_item("text_encoder", "rust_nfd_phf_v1")?;
    info.set_item("image_encoder", "rust_prefix_quadtree_v1")?;
    info.set_item("image_decoder", "rust_enhanced_quadtree_v1")?;
    info.set_item("build_profile", BUILD_PROFILE)?;
    Ok(info.unbind())
}

#[pyfunction]
fn encode_text(py: Python<'_>, text: String) -> Vec<u32> {
    py.allow_threads(move || encode_text_native(&text))
}

#[pyfunction]
fn encode_quadtree(
    py: Python<'_>,
    image_data: Vec<u8>,
    width: u32,
    height: u32,
    bit_depth: u8,
    threshold: f32,
) -> PyResult<(Vec<u32>, (u32, u32, u32, u8, u32))> {
    let (words, meta) = py.allow_threads(move || {
        encode_quadtree_native(&image_data, width, height, bit_depth, threshold)
    })?;
    Ok((
        words,
        (
            meta.width,
            meta.height,
            meta.root,
            meta.bit_depth,
            meta.threshold_x10,
        ),
    ))
}

#[pyfunction]
fn decode_quadtree(
    py: Python<'_>,
    words: Vec<u32>,
) -> PyResult<(Vec<u8>, (u32, u32, u32, u8, u32))> {
    let (image_bytes, meta) = py.allow_threads(move || decode_quadtree_native(&words))?;
    Ok((
        image_bytes,
        (
            meta.width,
            meta.height,
            meta.root,
            meta.bit_depth,
            meta.threshold_x10,
        ),
    ))
}

#[pyfunction]
#[pyo3(signature = (stream, record_invalid = false))]
fn scan_stream(
    py: Python<'_>,
    stream: &Bound<'_, PyAny>,
    record_invalid: bool,
) -> PyResult<Py<PyDict>> {
    let state = match try_collect_fast_words(stream)? {
        Some(words) => py.allow_threads(|| run_scan_words(&words, record_invalid)),
        _ => {
            let items = collect_items(stream)?;
            py.allow_threads(|| run_scan(&items, record_invalid))
        }
    };
    scan_state_to_py(py, state)
}

#[pyfunction]
#[pyo3(signature = (streams, record_invalid = false))]
fn scan_stream_batch(
    py: Python<'_>,
    streams: Vec<Vec<u32>>,
    record_invalid: bool,
) -> PyResult<Vec<Py<PyDict>>> {
    let states: Vec<ScanState> = py.allow_threads(move || {
        streams
            .par_iter()
            .map(|words| run_scan_words(words, record_invalid))
            .collect()
    });
    states
        .into_iter()
        .map(|state| scan_state_to_py(py, state))
        .collect()
}

#[pymodule]
fn zpe_imc_kernel(_py: Python<'_>, module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add("__version__", env!("CARGO_PKG_VERSION"))?;
    module.add("WORD_MASK", WORD_MASK)?;
    module.add_class::<NativeBuffer>()?;
    module.add_function(wrap_pyfunction!(configure_normal_words, module)?)?;
    module.add_function(wrap_pyfunction!(backend_info, module)?)?;
    module.add_function(wrap_pyfunction!(encode_text, module)?)?;
    module.add_function(wrap_pyfunction!(encode_quadtree, module)?)?;
    module.add_function(wrap_pyfunction!(decode_quadtree, module)?)?;
    module.add_function(wrap_pyfunction!(scan_stream, module)?)?;
    module.add_function(wrap_pyfunction!(scan_stream_batch, module)?)?;
    Ok(())
}
