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

/// Computes D8 Flow Direction.
/// Directions: 1=E, 2=NE, 3=N, 4=NW, 5=W, 6=SW, 7=S, 8=SE, 0=None
#[pyfunction]
#[pyo3(signature = (dem))]
fn compute_flow_direction<'py>(
    _py: Python<'py>,
    dem: PyReadonlyArray2<'py, f32>,
) -> PyResult<Bound<'py, PyArray2<i32>>> {
    let dem_view = dem.as_array();
    let (rows, cols) = dem_view.dim();
    let mut fdir = Array2::<i32>::zeros((rows, cols));

    let dr = [0, -1, -1, -1, 0, 1, 1, 1];
    let dc = [1, 1, 0, -1, -1, -1, 0, 1];
    let codes = [1, 2, 3, 4, 5, 6, 7, 8];

    for r in 0..rows {
        for c in 0..cols {
            let mut min_elev = dem_view[[r, c]];
            let mut best_code = 0;

            for i in 0..8 {
                let nr = r as i32 + dr[i];
                let nc = c as i32 + dc[i];
                if nr >= 0 && nr < rows as i32 && nc >= 0 && nc < cols as i32 {
                    let elev = dem_view[[nr as usize, nc as usize]];
                    if elev < min_elev {
                        min_elev = elev;
                        best_code = codes[i];
                    }
                }
            }
            fdir[[r, c]] = best_code;
        }
    }
    Ok(fdir.into_pyarray(_py))
}

/// Computes Flow Accumulation given Flow Direction.
#[pyfunction]
#[pyo3(signature = (fdir))]
fn compute_accumulation_from_fdir<'py>(
    _py: Python<'py>,
    fdir: PyReadonlyArray2<'py, i32>,
) -> PyResult<Bound<'py, PyArray2<f32>>> {
    let fdir_view = fdir.as_array();
    let (rows, cols) = fdir_view.dim();
    
    // Compute in-degree
    let mut in_degree = Array2::<i32>::zeros((rows, cols));
    let dr = [0, -1, -1, -1, 0, 1, 1, 1];
    let dc = [1, 1, 0, -1, -1, -1, 0, 1];

    for r in 0..rows {
        for c in 0..cols {
            let code = fdir_view[[r, c]];
            if code > 0 {
                let nr = r as i32 + dr[(code - 1) as usize];
                let nc = c as i32 + dc[(code - 1) as usize];
                if nr >= 0 && nr < rows as i32 && nc >= 0 && nc < cols as i32 {
                    in_degree[[nr as usize, nc as usize]] += 1;
                }
            }
        }
    }

    // Topological sort (Kahn's algorithm) for accumulation
    let mut accumulation = Array2::<f32>::from_elem((rows, cols), 1.0);
    let mut stack = Vec::new();

    for r in 0..rows {
        for c in 0..cols {
            if in_degree[[r, c]] == 0 {
                stack.push((r, c));
            }
        }
    }

    while let Some((r, c)) = stack.pop() {
        let code = fdir_view[[r, c]];
        if code > 0 {
            let nr = (r as i32 + dr[(code - 1) as usize]) as usize;
            let nc = (c as i32 + dc[(code - 1) as usize]) as usize;
            
            accumulation[[nr, nc]] += accumulation[[r, c]];
            in_degree[[nr, nc]] -= 1;
            if in_degree[[nr, nc]] == 0 {
                stack.push((nr, nc));
            }
        }
    }

    Ok(accumulation.into_pyarray(_py))
}

/// Traces a path downstream from a starting point.
#[pyfunction]
#[pyo3(signature = (fdir, start_r, start_c))]
fn trace_path(
    fdir: PyReadonlyArray2<i32>,
    start_r: usize,
    start_c: usize,
) -> PyResult<Vec<(usize, usize)>> {
    let fdir_view = fdir.as_array();
    let (rows, cols) = fdir_view.dim();
    let mut path = Vec::new();
    let mut curr_r = start_r;
    let mut curr_c = start_c;

    let dr = [0, -1, -1, -1, 0, 1, 1, 1];
    let dc = [1, 1, 0, -1, -1, -1, 0, 1];

    while curr_r < rows && curr_c < cols {
        path.push((curr_r, curr_c));
        let code = fdir_view[[curr_r, curr_c]];
        if code <= 0 { break; }
        
        let nr = curr_r as i32 + dr[(code - 1) as usize];
        let nc = curr_c as i32 + dc[(code - 1) as usize];
        
        if nr < 0 || nr >= rows as i32 || nc < 0 || nc >= cols as i32 { break; }
        
        let nr = nr as usize;
        let nc = nc as usize;
        if nr == curr_r && nc == curr_c { break; } // Loop safety
        if path.contains(&(nr, nc)) { break; } // Cycle safety
        
        curr_r = nr;
        curr_c = nc;
    }

    Ok(path)
}

#[pymodule]
fn georust_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(fill_depressions, m)?)?;
    m.add_function(wrap_pyfunction!(compute_flow_direction, m)?)?;
    m.add_function(wrap_pyfunction!(compute_accumulation_from_fdir, m)?)?;
    m.add_function(wrap_pyfunction!(trace_path, m)?)?;
    Ok(())
}
