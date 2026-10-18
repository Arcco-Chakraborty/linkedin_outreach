# Project notes

The app has a CLI (`main.py`) and Streamlit UI (`ui.py`, launched by `run_ui.py`).
Shared orchestration lives in `src/runner.py`, browser authentication in
`src/session.py`, and the current Apollo email lookup pipeline in `src/pipeline.py`
and `src/apollo_client.py`. CSV writing is in `src/sheets_writer.py`.

Use README.md for setup and docs/HANDOFF.md for the current work state.

Only synthetic demonstration data belongs in version control. Runtime `.env`,
cookie jars, credentials, scraped contacts, outputs, logs and bytecode are local
and ignored. `examples/` contains invented CSV records; the cookie example is
empty. The existing browser login and environment-variable interfaces are unchanged.

The old design/implementation notes under docs/superpowers describe proposed and
historical workflows, not a guarantee that every described feature is implemented.
