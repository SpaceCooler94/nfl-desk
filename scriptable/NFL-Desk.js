// Variables used by Scriptable.
// These must be at the very top of the file. Do not edit.
// icon-color: blue; icon-glyph: football;
// NFL Desk — game sheet. Fetches feed/current.json.
// Private repo: Keychain.set("nflDeskGithubToken", "ghp_...")

const OWNER = "SpaceCooler94";
const REPO = "nfl-desk";
const BRANCH = "main";
const FEED_PATH = "feed/current.json";
const SPORT = "nfl";
const NAMES = {DET:"LIONS",BUF:"BILLS",CAR:"PANTHERS",ATL:"FALCONS",MIN:"VIKINGS",CHI:"BEARS",PHI:"EAGLES",TEN:"TITANS",PIT:"STEELERS",NE:"PATRIOTS",GB:"PACKERS",NYJ:"JETS",CLE:"BROWNS",TB:"BUCCANEERS",NO:"SAINTS",BAL:"RAVENS",CIN:"BENGALS",HOU:"TEXANS",JAX:"JAGUARS",DEN:"BRONCOS",LV:"RAIDERS",LAC:"CHARGERS",MIA:"DOLPHINS",SF:"49ERS",SEA:"SEAHAWKS",ARI:"CARDINALS",WSH:"COMMANDERS",DAL:"COWBOYS",IND:"COLTS",KC:"CHIEFS",NYG:"GIANTS",LAR:"RAMS"};

function feedUrl() {
  return "https://raw.githubusercontent.com/" + OWNER + "/" + REPO + "/" + BRANCH + "/" + FEED_PATH + "?t=" + Date.now();
}
function apiUrl() {
  return "https://api.github.com/repos/" + OWNER + "/" + REPO + "/contents/" + FEED_PATH + "?ref=" + BRANCH;
}
function token() {
  try { if (Keychain.contains("nflDeskGithubToken")) return Keychain.get("nflDeskGithubToken"); } catch (e) {}
  return null;
}
async function loadCard() {
  const hdrs = { "User-Agent": "nfl-desk-scriptable" };
  const tok = token();
  if (tok) hdrs.Authorization = "Bearer " + tok;
  try {
    const raw = new Request(feedUrl());
    raw.headers = hdrs;
    raw.timeoutInterval = 20;
    return await raw.loadJSON();
  } catch (err) {
    const req = new Request(apiUrl());
    req.headers = Object.assign({}, hdrs, { Accept: "application/vnd.github.raw+json" });
    req.timeoutInterval = 20;
    return await req.loadJSON();
  }
}
function nameOf(ab) { return NAMES[ab] || ab || ""; }
function grade(p) {
  const z = p.sigma ? Math.abs(Number(p.edge) || 0) / Number(p.sigma) : Math.abs(Number(p.edge) || 0);
  if (p.play === "OVER" || p.play === "UNDER") return "A";
  if (p.play === "WATCH" && z >= 0.45) return "A-";
  if (p.play === "WATCH") return "B+";
  return "C";
}
function fmt(n) {
  if (n == null || isNaN(Number(n))) return "—";
  const v = Number(n);
  return (v > 0 ? "+" : "") + v.toFixed(1);
}
function gamesFrom(card) {
  const m = new Map();
  (card.games || []).forEach((g) => m.set(g.id, g));
  (card.props || []).forEach((p) => {
    if (!m.has(p.game_id)) m.set(p.game_id, { id: p.game_id, away: p.team, home: p.opp, when: p.when });
  });
  return [...m.values()];
}
function propsFor(card, gid) {
  return (card.props || []).filter((p) => p.game_id === gid).sort((a, b) => Math.abs(b.edge || 0) - Math.abs(a.edge || 0));
}
function esc(s) {
  return String(s == null ? "" : s).replace(/&/g, "&").replace(/</g, "<").replace(/"/g, """);
}
function pill(k, v) {
  return "<div class=\"pill\"><div class=\"k\">" + esc(k) + "</div><div class=\"v\">" + esc(String(v)) + "</div></div>";
}
function lookCol(team, rows) {
  const body = rows.slice(0, 4).map((p) => {
    const z = Math.abs(Number(p.edge) || 0);
    const cls = (p.sigma && z / p.sigma >= 0.6) || z >= 12 ? "g" : z >= 6 ? "y" : "r";
    const score = p.p_over != null ? Math.round(Number(p.p_over) * 100) : Math.min(99, Math.round(50 + z));
    return "<div class=\"mrow\"><div><div class=\"pn\">" + esc(p.player) + "</div><div class=\"ps\">" + esc(p.market_label || p.market) + " · " + esc(p.play) + "</div></div><div class=\"badge " + cls + "\">" + score + "</div></div>";
  }).join("") || "<div class=\"ps\">No tagged looks</div>";
  return "<div><div class=\"ps\">" + esc(team || "") + " LOOKS</div>" + body + "</div>";
}
function sheetHTML(card, g) {
  const rows = propsFor(card, g.id);
  const week = card.week ? ("WEEK " + card.week) : String(card.date || "").slice(5);
  const ai = g.away_implied != null ? ("IMPLIED " + g.away_implied) : "";
  const hi = g.home_implied != null ? ("IMPLIED " + g.home_implied) : "";
  const pills = pill("SPREAD", g.spread || "—") + pill("TOTAL", g.total != null ? g.total : "—") + pill("KICKOFF", g.when || "—") + pill("ROOF", g.roof || "—");
  const body = rows.map((p) => {
    const gapCls = Number(p.edge) >= 0 ? "pos" : "neg";
    return "<tr><td><div class=\"who\"><div class=\"dot\">" + (p.team || "") + "</div><div><div class=\"pn\">" + esc(p.player) + "</div><div class=\"ps\">" + esc(p.pos || "") + " · " + esc(p.market_label || p.market) + "</div></div></div></td><td class=\"num\">" + (p.proj != null ? p.proj : "—") + "</td><td class=\"num\">" + (p.line != null ? p.line : "—") + "</td><td class=\"num " + gapCls + "\">" + fmt(p.edge) + "</td><td class=\"num grade\">" + grade(p) + "</td></tr>";
  }).join("") || "<tr><td colspan=\"5\" class=\"ps\">No props</td></tr>";
  return "<!DOCTYPE html><html><head><meta charset=\"utf-8\"/><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"/><style>body{margin:0;background:#0b0d12;color:#f4f6fb;font:14px/1.4 -apple-system}:root{--pink:#ff2d7b;--good:#3DDC97;--bad:#ff6b6b;--card:#12151c;--line:#232833;--mute:#9aa3b2}.wrap{padding:18px 14px 36px}.kicker{display:flex;justify-content:space-between;align-items:center}.kicker b{background:#1b1f28;padding:3px 7px;border-radius:4px;margin-right:8px;font-size:11px}.logo{font-weight:800;font-size:22px}.logo span{color:var(--pink)}h1{font-size:26px;margin:10px 0 6px}.meta{color:var(--mute);font-size:11px;letter-spacing:.06em;text-transform:uppercase}.teams{display:grid;grid-template-columns:1fr 36px 1fr;margin:14px 0 10px;border-radius:10px;overflow:hidden}.away{background:linear-gradient(90deg,#08363c,#0f4b52);padding:14px}.home{background:linear-gradient(90deg,#8a3414,#c24a18);padding:14px;text-align:right}.lab{font-size:10px;opacity:.8}.nm{font-size:16px;font-weight:800}.imp{font-size:11px;opacity:.85}.at{display:grid;place-items:center;font-weight:800}.pills{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-bottom:12px}.pill{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 6px;text-align:center}.pill .k{font-size:9px;color:var(--mute)}.pill .v{font-size:13px;font-weight:800;margin-top:3px}.panel{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px;margin-bottom:10px}.ph{margin-bottom:6px;font-size:12px}.ph b{border-left:3px solid var(--pink);padding-left:8px}table{width:100%;border-collapse:collapse}th{text-align:left;font-size:10px;color:var(--mute);padding:6px}td{padding:9px 6px;border-top:1px solid var(--line)}.num{text-align:right}.who{display:flex;gap:8px;align-items:center}.dot{width:20px;height:20px;border-radius:50%;background:#1d222c;display:grid;place-items:center;font-size:8px;font-weight:800}.pn{font-weight:700}.ps{font-size:11px;color:var(--mute)}.pos{color:var(--good);font-weight:700}.neg{color:var(--bad);font-weight:700}.grade{font-weight:800;color:var(--pink)}.cols{display:grid;grid-template-columns:1fr 1fr;gap:8px}.mrow{display:flex;justify-content:space-between;padding:7px 2px;border-top:1px solid var(--line)}.badge{min-width:32px;text-align:center;font-weight:800;padding:3px 5px;border-radius:6px}.g{background:#14351f;color:#3DDC97}.y{background:#3a3210;color:#e8c547}.r{background:#3a1515;color:#ff6b6b}.foot{display:flex;justify-content:space-between;color:var(--mute);font-size:11px}.foot b{color:var(--pink)}</style></head><body><div class=\"wrap\"><div class=\"kicker\"><div><b>" + esc(week) + "</b> NFL · GAME SHEET</div><div class=\"logo\"><span>x</span>DESK</div></div><h1>" + esc(nameOf(g.away)) + " AT " + esc(nameOf(g.home)) + "</h1><div class=\"meta\">" + esc([g.when || "", g.tv || "", g.venue || ""].filter(Boolean).join(" · ")) + "</div><div class=\"teams\"><div class=\"away\"><div class=\"lab\">AWAY</div><div class=\"nm\">" + esc(nameOf(g.away)) + "</div><div class=\"imp\">" + esc(ai) + "</div></div><div class=\"at\">AT</div><div class=\"home\"><div class=\"lab\">HOME</div><div class=\"nm\">" + esc(nameOf(g.home)) + "</div><div class=\"imp\">" + esc(hi) + "</div></div></div><div class=\"pills\">" + pills + "</div><div class=\"panel\"><div class=\"ph\"><b>PROPS AT A GLANCE</b></div><table><thead><tr><th>PLAYER</th><th class=\"num\">PROJ</th><th class=\"num\">LINE</th><th class=\"num\">GAP</th><th class=\"num\">GRADE</th></tr></thead><tbody>" + body + "</tbody></table></div><div class=\"panel\"><div class=\"ph\"><b>KEY LOOKS</b></div><div class=\"cols\">" + lookCol(g.home, rows.filter((p) => p.team === g.home)) + lookCol(g.away, rows.filter((p) => p.team === g.away)) + "</div></div><div class=\"foot\"><div><b>desk</b> · research</div><div>" + esc(card.status || "") + "</div></div></div></body></html>";
}
async function presentSheet(card, g) {
  const wv = new WebView();
  await wv.loadHTML(sheetHTML(card, g));
  await wv.present(true);
}
async function pickGame(card) {
  const games = gamesFrom(card);
  const table = new UITable();
  table.showSeparators = true;
  const head = new UITableRow();
  head.isHeader = true;
  head.addText("NFL  GAME SHEETS");
  table.addRow(head);
  for (const g of games) {
    const n = propsFor(card, g.id).length;
    const row = new UITableRow();
    row.height = 52;
    row.dismissOnSelect = true;
    row.onSelect = async () => { await presentSheet(card, g); };
    const t = row.addText(nameOf(g.away) + " AT " + nameOf(g.home) + "\n" + (g.when || "") + " · " + n + " props");
    t.titleFont = Font.boldSystemFont(15);
    t.subtitleFont = Font.systemFont(11);
    table.addRow(row);
  }
  await table.present();
}
function buildWidget(card) {
  const w = new ListWidget();
  w.backgroundColor = new Color("#0b0d12");
  w.setPadding(12, 14, 12, 14);
  const games = gamesFrom(card);
  const g = games.find((x) => String(x.when || "").indexOf("FINAL") === -1) || games[0] || {};
  const p = propsFor(card, g.id)[0];
  const k = w.addText((card.week ? ("WEEK " + card.week) : "") + "  ·  GAME SHEET");
  k.font = Font.boldSystemFont(10);
  k.textColor = new Color("#9aa3b2");
  const title = w.addText(nameOf(g.away) + " AT " + nameOf(g.home));
  title.font = Font.boldSystemFont(16);
  title.textColor = Color.white();
  title.minimumScaleFactor = 0.6;
  const sub = w.addText((g.spread || "") + "   " + (g.total != null ? g.total : ""));
  sub.font = Font.systemFont(11);
  sub.textColor = new Color("#9aa3b2");
  w.addSpacer(8);
  if (p) {
    const nm = w.addText(p.player);
    nm.font = Font.boldSystemFont(15);
    nm.textColor = Color.white();
    const gap = w.addText((p.market_label || p.market) + "  " + (p.proj != null ? p.proj : "—") + " vs " + (p.line != null ? p.line : "—") + "  " + fmt(p.edge) + "  " + grade(p));
    gap.font = Font.mediumSystemFont(11);
    gap.textColor = Number(p.edge) >= 0 ? new Color("#3DDC97") : new Color("#ff6b6b");
  }
  w.addSpacer();
  const f = w.addText("xDESK  ·  " + (card.status || ""));
  f.font = Font.boldSystemFont(10);
  f.textColor = new Color("#ff2d7b");
  return w;
}
async function run() {
  let card;
  try { card = await loadCard(); }
  catch (e) {
    if (config.runsInWidget) { const w = new ListWidget(); w.addText("Feed failed"); Script.setWidget(w); Script.complete(); return; }
    const a = new Alert(); a.title = "NFL Desk feed failed"; a.message = String(e); a.addAction("OK"); await a.present(); Script.complete(); return;
  }
  if (config.runsInWidget) { Script.setWidget(buildWidget(card)); Script.complete(); return; }
  await pickGame(card);
  Script.complete();
}
await run();
