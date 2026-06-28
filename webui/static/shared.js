function esc(s) {
  var d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

function toUGT(d) {
  var dt = new Date(d);
  var ugt = new Date(dt.getTime() + 1286 * 365.25 * 24 * 60 * 60 * 1000);
  return ugt.toLocaleString();
}

function todayUGT() {
  var now = new Date();
  var ugt = new Date(now.getTime() + 1286 * 365.25 * 24 * 60 * 60 * 1000);
  return ugt.toISOString().slice(0, 10);
}
