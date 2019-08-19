from tornasole import modes
import shutil, os
import numpy as np
from tornasole.trials import create_trial
from tornasole.core.tensor import StepState
from datetime import datetime
from tornasole.core.writer import FileWriter
from tornasole.core.collection_manager import CollectionManager

def test_modes_on_global_data():
  pass # other tests in create, local, s3 do this


def test_mode_data():
  run_id = 'trial_' + datetime.now().strftime('%Y%m%d-%H%M%S%f')
  path = 'ts_outputs'

  c = CollectionManager()
  c.add("default")
  c.get("default").tensor_names = ["arr"]
  c.export(os.path.join(path, run_id, "collections.ts"))
  tr = create_trial('ts_outputs/' + run_id)

  for s in range(0, 10):
    fw = FileWriter(logdir='ts_outputs', trial=run_id, step=s)
    if s % 2 == 0:
      fw.write_tensor(tdata=np.array([[1.0, 2.0], [3.0, 4.0]],
                                     dtype=np.float32),
                      tname='arr', mode=modes.TRAIN,
                      mode_step=s // 2)
    else:
      fw.write_tensor(tdata=np.array([[1.0, 2.0], [3.0, 4.0]],
                                     dtype=np.float32),
                      tname='arr', mode=modes.EVAL,
                      mode_step=s // 2)
    fw.close()

    if s % 2 == 0:
      assert tr.has_passed_step(s // 2, mode=modes.TRAIN) == StepState.AVAILABLE
      assert tr.has_passed_step(s // 2, mode=modes.EVAL) == StepState.NOT_YET_AVAILABLE
    else:
      assert tr.has_passed_step(s // 2, mode=modes.EVAL) == StepState.AVAILABLE

    assert tr.has_passed_step(s) == StepState.AVAILABLE
    assert tr.has_passed_step(s+1) == StepState.NOT_YET_AVAILABLE
    assert tr.has_passed_step(s + 1, mode=modes.TRAIN) == StepState.NOT_YET_AVAILABLE

  assert len(tr.tensors()) == 1
  assert len(tr.available_steps()) == 10
  assert len(tr.available_steps(mode=modes.TRAIN)) == 5
  assert len(tr.available_steps(mode=modes.EVAL)) == 5
  assert len(tr.modes()) == 2

  for i in range(10):
    if i % 2 == 0:
      assert tr.mode(i) == modes.TRAIN
    else:
      assert tr.mode(i) == modes.EVAL
    assert tr.mode_step(i) == i//2

  for i in range(5):
    assert tr.global_step(modes.TRAIN, i) == (i * 2)
    assert tr.global_step(modes.EVAL, i) == (i * 2) + 1

  assert len(tr.tensor('arr').steps()) == 10
  assert len(tr.tensor('arr').steps(mode=modes.TRAIN)) == 5
  assert len(tr.tensor('arr').steps(mode=modes.EVAL)) == 5

  for i in range(10):
    assert tr.tensor('arr').value(i) is not None
    if i < 5 :
      assert tr.tensor('arr').value(i, mode=modes.TRAIN) is not None
      assert tr.tensor('arr').value(i, mode=modes.EVAL) is not None

  shutil.rmtree('ts_outputs/' + run_id)