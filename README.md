<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>311 Street Lamp Dashboard — Staten Island</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f1923; color: #e0e0e0; }
  .header { background: linear-gradient(135deg, #1a2a3a 0%, #0d1b2a 100%); padding: 24px 40px; border-bottom: 3px solid #00b4d8; display: flex; align-items: center; justify-content: space-between; }
  .header h1 { font-size: 1.6rem; color: #00b4d8; }
  .header .subtitle { font-size: 0.85rem; color: #8899aa; margin-top: 4px; }
  .header .badge { background: #00b4d8; color: #0f1923; padding: 6px 16px; border-radius: 20px; font-weight: 700; font-size: 0.8rem; }
  .tabs { display: flex; background: #1a2a3a; border-bottom: 2px solid #223344; padding: 0 40px; }
  .tab { padding: 14px 28px; cursor: pointer; font-size: 0.9rem; color: #8899aa; border-bottom: 3px solid transparent; transition: all 0.3s; }
  .tab:hover { color: #00b4d8; }
  .tab.active { color: #00b4d8; border-bottom-color: #00b4d8; font-weight: 600; }
  .dashboard { padding: 30px 40px; display: none; }
  .dashboard.active { display: block; }
  .kpi-row { display: grid; grid-template-columns: repeat(5, 1fr); gap: 20px; margin-bottom: 30px; }
  .kpi-card { background: linear-gradient(135deg, #1a2a3a, #162232); border: 1px solid #223344; border-radius: 12px; padding: 20px; text-align: center; }
  .kpi-card .value { font-size: 2rem; font-weight: 700; color: #00b4d8; }
  .kpi-card .label { font-size: 0.78rem; color: #8899aa; margin-top: 6px; text-transform: uppercase; letter-spacing: 1px; }
  .kpi-card .change { font-size: 0.75rem; margin-top: 4px; }
  .change.up { color: #e63946; }
  .change.down { color: #2ec4b6; }
  .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 30px; }
  .grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 24px; margin-bottom: 30px; }
  .card { background: #1a2a3a; border: 1px solid #223344; border-radius: 12px; padding: 24px; }
  .card h3 { font-size: 1rem; color: #00b4d8; margin-bottom: 16px; border-bottom: 1px solid #223344; padding-bottom: 10px; }
  .chart-container { position: relative; width: 100%; height: 300px; }
  
  table { width: 100%; border-collapse: collapse; font-size: 0.82rem; }
  th { background: #0d1b2a; color: #00b4d8; padding: 10px 12px; text-align: left; position: sticky; top: 0; z-index: 2; }
  td { padding: 9px 12px; border-bottom: 1px solid #223344; }
  tr:hover { background: rgba(0,180,216,0.05); }
  
  .status-badge { padding: 3px 10px; border-radius: 12px; font-size: 0.72rem; font-weight: 600; }
  .status-open { background: rgba(230,57,70,0.2); color: #e63946; }
  .status-progress { background: rgba(255,183,3,0.2); color: #ffb703; }
  .status-closed { background: rgba(46,196,182,0.2); color: #2ec4b6; }

  /* Classifier & Similarity Search */
  .clf-textarea { width: 100%; background: #0d1b2a; border: 1px solid #334455; color: #e0e0e0; padding: 14px 16px; border-radius: 10px; font-size: 0.95rem; min-height: 80px; }
  .btn { background: #00b4d8; color: #0f1923; border: none; padding: 11px 28px; border-radius: 8px; font-weight: 700; cursor: pointer; transition: 0.3s; }
  .sim-complaint-card { background: #0d1b2a; border: 1px solid #223344; border-radius: 10px; padding: 16px; margin-bottom: 12px; cursor: pointer; transition: 0.3s; }
  .sim-complaint-card:hover { border-color: #00b4d8; transform: translateX(4px); }
</style>
</head>
<body>

<div class="header">
  <div>
    <h1>🔦 311 Street Lamp Complaints — Staten Island</h1>
    <div class="subtitle">NYC Open Data Dashboard • Complaint Classification & Similarity Search</div>
  </div>
  <div class="badge">MOCK DATA • v2.0</div>
</div>

<div class="tabs">
  <div class="tab active" onclick="switchTab('overview', this)">📊 Overview</div>
  <div class="tab" onclick="switchTab('classifier', this)">🏷️ Classifier</div>
  <div class="tab" onclick="switchTab('similarity', this)">🔍 Similarity Search</div>
  <div class="tab" onclick="switchTab('vendors', this)">🏢 Vendors</div>
  <div class="tab" onclick="switchTab('calls', this)">📋 All Calls</div>
</div>

<script>
  // ========== TAB SWITCHING ==========
  function switchTab(tab, el) {
    document.querySelectorAll('.dashboard').forEach(d => d.classList.remove('active'));
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.getElementById('tab-' + tab).classList.add('active');
    el.classList.add('active');
  }

  // Dashboard Logic and Data Initialization goes here...
</script>

</body>
</html>
