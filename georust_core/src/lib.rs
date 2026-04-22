use pyo3::prelude::*;
use numpy::{PyArray2, PyReadonlyArray2, IntoPyArray};
use ndarray::prelude::*;

/// Formats the sum of two numbers as string.
#[pyfunction]
fn sum_as_string(a: usize, b: usize) -> PyResult<String> {
    Ok((a + b).to_string())
}

/// Placeholder for Flow Direction computation
#[pyfunction]
fn compute_flow_direction(dem: PyReadonlyArray2<f32>) -> PyResult<PyObject> {
    let dem = dem.as_array();
    // TODO: Implement Priority-Flood algorithm
    let shape = dem.dim();
    let result = Array2::<i32>::zeros(shape);
    
    Python::with_gil(|py| {
        Ok(result.into_pyarray(py).to_object(py))
    })
}

/// A Python module implemented in Rust.
#[pymodule]
fn georust_core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(sum_as_string, m)?)?;
    m.add_function(wrap_pyfunction!(compute_flow_direction, m)?)?;
    Ok(())
}
