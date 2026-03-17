# Technical Architecture

## Current stack
- Python
- Streamlit
- OpenAI API
- Vector stores
- Custom audit engine
- Local and database-based access logic
- CSV / DOCX / PDF export

## Current main files
- aia_web.py
- audit_engine.py
- db.py
- ui_config.py
- isometric_requirements.py

## Current challenges
- main interface file is too large
- persistence is not yet fully implemented
- navigation is still limited
- product modes are not yet separated
- methodology data model is not yet generalized

## Direction
The system should evolve toward:
- project-centric architecture
- persistent audit history
- reusable analysis modes
- modular methodology framework
- reusable filler tools
