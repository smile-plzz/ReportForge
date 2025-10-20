PY=python
VENv=.venv
ACT=source $(VENv)/bin/activate

install:
	$(PY) -m venv $(VENv)
	. $(VENv)/bin/activate && pip install -r requirements.txt

run:
	. $(VENv)/bin/activate && $(PY) src/report.py --csv ./tests/sample_comments.csv --tz Asia/Dhaka --out ./out
