use pyo3::exceptions::{PyRuntimeError, PyValueError};
use pyo3::prelude::*;

use crate::{MotionMode, VibrationTable};

#[pyclass(name = "VibrationTable")]
struct PyVibrationTable {
    inner: VibrationTable,
}

#[pymethods]
impl PyVibrationTable {
    #[new]
    fn new(addr: &str) -> PyResult<Self> {
        Ok(Self {
            inner: VibrationTable::connect(addr).map_err(to_py_error)?,
        })
    }

    #[staticmethod]
    fn can_connect(addr: &str) -> bool {
        VibrationTable::can_connect(addr)
    }

    fn start_vibration(&mut self, mode: &str) -> PyResult<()> {
        self.inner
            .start_vibration(parse_mode(mode)?)
            .map_err(to_py_error)
    }

    fn start_vibration_with_params(
        &mut self,
        mode: &str,
        frequency: u16,
        amplitude: u16,
    ) -> PyResult<()> {
        self.inner
            .start_vibration_with_params(parse_mode(mode)?, frequency, amplitude)
            .map_err(to_py_error)
    }

    fn stop_vibration(&mut self) -> PyResult<()> {
        self.inner.stop_vibration().map_err(to_py_error)
    }

    fn light_on(&mut self, brightness: u16) -> PyResult<()> {
        self.inner.light_on(brightness).map_err(to_py_error)
    }

    fn light_off(&mut self) -> PyResult<()> {
        self.inner.light_off().map_err(to_py_error)
    }

    fn read_faults(&mut self) -> PyResult<u16> {
        self.inner.read_faults().map_err(to_py_error)
    }

    fn has_fault(&mut self) -> PyResult<bool> {
        self.inner.has_fault().map_err(to_py_error)
    }

    fn clear_faults(&mut self) -> PyResult<()> {
        self.inner.clear_faults().map_err(to_py_error)
    }
}

#[pymodule]
fn flexible_vibration_table(_py: Python<'_>, module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_class::<PyVibrationTable>()?;
    Ok(())
}

fn parse_mode(mode: &str) -> PyResult<MotionMode> {
    match mode {
        "MoveRight" => Ok(MotionMode::MoveRight),
        "MoveLeft" => Ok(MotionMode::MoveLeft),
        "MoveForward" => Ok(MotionMode::MoveForward),
        "MoveBackward" => Ok(MotionMode::MoveBackward),
        "MoveUpperRight" => Ok(MotionMode::MoveUpperRight),
        "MoveUpperLeft" => Ok(MotionMode::MoveUpperLeft),
        "MoveLowerLeft" => Ok(MotionMode::MoveLowerLeft),
        "MoveLowerRight" => Ok(MotionMode::MoveLowerRight),
        "Bounce" => Ok(MotionMode::Bounce),
        "CenterHorizontal" => Ok(MotionMode::CenterHorizontal),
        "CenterVertical" => Ok(MotionMode::CenterVertical),
        "CenterDiagonalUp" => Ok(MotionMode::CenterDiagonalUp),
        "CenterDiagonalDown" => Ok(MotionMode::CenterDiagonalDown),
        _ => Err(PyValueError::new_err(format!(
            "unknown motion mode: {mode}"
        ))),
    }
}

fn to_py_error(error: crate::Error) -> PyErr {
    PyRuntimeError::new_err(format!("{error:?}"))
}
