MachineCare update

This update adds five demo machines with sensor readings and health predictions:
- CNC Machine 01 — Healthy
- Lathe Machine 01 — Warning
- Milling Machine 01 — Critical
- Drilling Machine 01 — Healthy
- Grinding Machine 01 — Warning

The data is seeded automatically the first time the dashboard is opened. Existing records are preserved and the demo records are not duplicated on refresh.

Replace app.py, templates/index.html and static/style.css in the existing project, then deploy:
railway up --service MachineHealthWeb
