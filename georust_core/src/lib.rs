use pyo3::prelude::*;
use numpy::{PyArray2, PyReadonlyArray2, IntoPyArray};
use ndarray::prelude::*;
use std::collections::BinaryHeap;
use std::cmp::Ordering;

#[derive(Copy, Clone, PartialEq)]
struct Node {
    row: usize,
    col: usize,
    elevation: f32,
}

impl Eq for Node {}

impl Ord for Node {
    fn cmp(&self, other: &Self) -> Ordering {
        // Reverse for min-heap (lowest elevation first)
        other.elevation.partial_cmp(&self.elevation).unwrap_or(Ordering::Equal)
    }
}

impl PartialOrd for Node {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

/// Fills depressions in a DEM using the Priority-Flood algorithm.
#[pyfunction]
#[pyo3(signature = (dem))]
fn fill_depressions<'py>(
    _py: Python<'py>,
    dem: PyReadonlyArray2<'py, f32>,
) -> PyResult<Bound<'py, PyArray2<f32>>> {
    let dem_view = dem.as_array();
    let (rows, cols) = dem_view.dim();
    let mut filled = dem_view.to_owned();
    let mut visited = Array2::<bool>::from_elem((rows, cols), false);
    let mut pq = BinaryHeap::new();

    // 1. Initialize priority queue with boundary cells
    for r in 0..rows {
        for c in [0, cols - 1] {
            pq.push(Node { row: r, col: c, elevation: filled[[r, c]] });
            visited[[r, c]] = true;
        }
    }
    for c in 1..cols - 1 {
        for r in [0, rows - 1] {
            pq.push(Node { row: r, col: c, elevation: filled[[r, c]] });
            visited[[r, c]] = true;
        }
    }

    // 2. Process queue
    let dr = [-1, -1, -1, 0, 0, 1, 1, 1];
    let dc = [-1, 0, 1, -1, 1, -1, 0, 1];

    while let Some(current) = pq.pop() {
        for i in 0..8 {
            let nr = current.row as i32 + dr[i];
            let nc = current.col as i32 + dc[i];

            if nr >= 0 && nr < rows as i32 && nc >= 0 && nc < cols as i32 {
                let nr = nr as usize;
                let nc = nc as usize;

                if !visited[[nr, nc]] {
                    if filled[[nr, nc]] < current.elevation {
                        filled[[nr, nc]] = current.elevation;
                    }
                    visited[[nr, nc]] = true;
                    pq.push(Node { row: nr, col: nc, elevation: filled[[nr, nc]] });
                }
            }
        }
    }

    Ok(filled.into_pyarray(_py))
}

/// Computes D8 Flow Direction and Flow Accumulation.
#[pyfunction]
#[pyo3(signature = (dem))]
fn compute_accumulation<'py>(
    _py: Python<'py>,
    dem: PyReadonlyArray2<'py, f32>,
) -> PyResult<Bound<'py, PyArray2<f32>>> {
    let dem_view = dem.as_array();
    let (rows, cols) = dem_view.dim();
    
    // Sort cells by elevation descending for accumulation computation
    let mut cells: Vec<Node> = Vec::with_capacity(rows * cols);
    for r in 0..rows {
        for c in 0..cols {
            cells.push(Node { row: r, col: c, elevation: dem_view[[r, c]] });
        }
    }
    // Sort descending: highest first
    cells.sort_by(|a, b| b.elevation.partial_cmp(&a.elevation).unwrap_or(Ordering::Equal));

    let mut accumulation = Array2::<f32>::from_elem((rows, cols), 1.0);
    
    for cell in cells {
        let r = cell.row;
        let c = cell.col;
        
        let mut min_elev = dem_view[[r, c]];
        let mut target = None;

        let dr = [-1, -1, -1, 0, 0, 1, 1, 1];
        let dc = [-1, 0, 1, -1, 1, -1, 0, 1];

        for i in 0..8 {
            let nr = r as i32 + dr[i];
            let nc = c as i32 + dc[i];

            if nr >= 0 && nr < rows as i32 && nc >= 0 && nc < cols as i32 {
                let nr = nr as usize;
                let nc = nc as usize;
                if dem_view[[nr, nc]] < min_elev {
                    min_elev = dem_view[[nr, nc]];
                    target = Some((nr, nc));
                }
            }
        }

        if let Some((tr, tc)) = target {
            accumulation[[tr, tc]] += accumulation[[r, c]];
        }
    }

    Ok(accumulation.into_pyarray(_py))
}

#[pymodule]
fn georust_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(fill_depressions, m)?)?;
    m.add_function(wrap_pyfunction!(compute_accumulation, m)?)?;
    Ok(())
}
