// Variables used by Scriptable.
// These must be at the very top of the file. Do not edit.
// icon-color: blue; icon-glyph: football;
// NFL Desk — xDESK game sheet. Team colors on banner + dots.

const OWNER = "SpaceCooler94";
const REPO = "nfl-desk";
const BRANCH = "main";
const FEED_PATH = "feed/current.json";
const TOKEN_KEY = "nflDeskGithubToken";

const NAMES = {
  DET: "LIONS", BUF: "BILLS", CAR: "PANTHERS", ATL: "FALCONS",
  MIN: "VIKINGS", CHI: "BEARS", PHI: "EAGLES", TEN: "TITANS",
  PIT: "STEELERS", NE: "PATRIOTS", GB: "PACKERS", NYJ: "JETS",
  CLE: "BROWNS", TB: "BUCCANEERS", NO: "SAINTS", BAL: "RAVENS",
  CIN: "BENGALS", HOU: "TEXANS", JAX: "JAGUARS", DEN: "BRONCOS",
  LV: "RAIDERS", LAC: "CHARGERS", MIA: "DOLPHINS", SF: "49ERS",
  SEA: "SEAHAWKS", ARI: "CARDINALS", WSH: "COMMANDERS", DAL: "COWBOYS",
  IND: "COLTS", KC: "CHIEFS", NYG: "GIANTS", LAR: "RAMS"
};

const COLORS = {
  ARI: ["#97233F", "#000000"], ATL: ["#A71930", "#000000"],
  BAL: ["#241773", "#9E7C0C"], BUF: ["#00338D", "#C60C30"],
  CAR: ["#0085CA", "#101820"], CHI: ["#0B162A", "#C83803"],
  CIN: ["#FB4F14", "#000000"], CLE: ["#311D00", "#FF3C00"],
  DAL: ["#003594", "#869397"], DEN: ["#002244", "#FB4F14"],
  DET: ["#0076B6", "#B0B7BC"], GB: ["#203731", "#FFB612"],
  HOU: ["#03202F", "#A71930"], IND: ["#002C5F", "#A2AAAD"],
  JAX: ["#006778", "#D7A22A"], KC: ["#E31837", "#FFB81C"],
  LV: ["#000000", "#A5ACAF"], LAC: ["#0080C6", "#FFC20E"],
  LAR: ["#003594", "#FFA300"], MIA: ["#008E97", "#FC4C02"],
  MIN: ["#4F2683", "#FFC62F"], NE: ["#002244", "#C60C30"],
  NO: ["#101820", "#D3BC8D"], NYG: ["#0B2265", "#A71930"],
  NYJ: ["#125740", "#FFFFFF"], PHI: ["#004C54", "#A5ACAF"],
  PIT: ["#101820", "#FFB612"], SF: ["#AA0000", "#B3995D"],
  SEA: ["#002244", "#69BE28"], TB: ["#D50A0A", "#34302B"],
  TEN: ["#0C2340", "#4B92DB"], WSH: ["#5A1414", "#FFB612"]
};

function feedUrl() {
  return "https://raw.githubusercontent.com/" + OWNER + "/" + REPO + "/" + BRANCH + "/" + FEED_PATH + "?t=" + Date.now();
}
function apiUrl() {
  return "https://api.github.com/repos/" + OWNER + "/" + REPO + "/contents/" + FEED_PATH + "?ref=" + BRANCH;
}
function token() {
  try { if (Keychain.contains(TOKEN_KEY)) return Keychain.get(TOKEN_KEY); } catch (e) {}
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
function palette(ab) { return COLORS[ab] || ["#1d232d", "#8b93a2"]; }
function inkFor(hex) {
  const h = String(hex || "").replace("#", "");
  if (h.length < 6) return "#f3f5f8";
  const r = parseInt(h.slice(0, 2), 16);
  const g = parseInt(h.slice(2, 4), 16);
  const b = parseInt(h.slice(4, 6), 16);
  return ((r * 299 + g * 587 + b * 114) / 1000) > 155 ? "#0a0c10" : "#f3f5f8";
}
function sideStyle(ab, align) {
  const c = palette(ab);
  return "background:linear-gradient(90deg," + c[0] + "," + c[1] + ");color:" + inkFor(c[0]) + ";padding:16px 14px;" + (align === "right" ? "text-align:right;" : "");
}
function dotStyle(ab) {
  const c = palette(ab);
  return "background:" + c[0] + ";color:" + inkFor(c[0]) + ";";
}
function fmt(n) {
  if (n === null || n === undefined || isNaN(Number(n))) return "—";
  const v = Number(n);
  return (v > 0 ? "+" : "") + v.toFixed(1);
}
function grade(p) {
  const z = p.sigma ? Math.abs(Number(p.edge) || 0) / Number(p.sigma) : Math.abs(Number(p.edge) || 0);
  if (p.play === "OVER" || p.play === "UNDER") return "A";
  if (p.play === "WATCH" && z >= 0.45) return "A-";
  if (p.play === "WATCH") return "B+";
  return "C";
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
  return (card.props || [])
    .filter((p) => p.game_id === gid)
    .sort((a, b) => Math.abs(b.edge || 0) - Math.abs(a.edge || 0));
}
function esc(s) {
  return String(s == null ? "" : s)
    .replace(/&/g, "&#38;")
    .replace(/</g, "&#60;")
    .replace(/"/g, "&#34;");
}
function badgeClass(score) {
  const n = Number(score);
  if (n >= 70) return "g";
  if (n <= 20) return "r";
  return "y";
}
function looksFor(g, rows) {
  if (g.looks && g.looks.length) return g.looks;
  return rows.slice(0, 8).map((p) => ({
    side: p.team === g.home ? "home" : "away",
    team: p.team,
    player: p.player,
    pos: p.pos || "",
    note: (p.market_label || p.market || "") + " · " + (p.play || ""),
    score: p.p_over != null ? Math.round(Number(p.p_over) * 100) : 50
  }));
}
function sheetCSS() {
  return ":root{--bg:#0a0c10;--ink:#f3f5f8;--mute:#8b93a2;--pink:#ff2d7b;--good:#3DDC97;--bad:#e35d6a}*{box-sizing:border-box}html,body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.35 -apple-system,system-ui,sans-serif}.wrap{max-width:920px;margin:0 auto;padding:16px 14px 48px}.kicker{display:flex;justify-content:space-between;align-items:center}.kicker-l{font-size:11px;letter-spacing:.14em;color:var(--mute);font-weight:700}.kicker-l b{display:inline-block;background:#1c212b;color:#fff;padding:3px 8px;border-radius:4px;margin-right:8px}.logo{font-weight:900;font-size:26px}.logo span{color:var(--pink)}h1{font-size:30px;margin:8px 0 6px;font-weight:800}.meta{color:var(--mute);font-size:11px;letter-spacing:.08em;text-transform:uppercase;margin-bottom:12px}.teams{display:grid;grid-template-columns:1fr 42px 1fr;border-radius:12px;overflow:hidden;margin-bottom:10px}.lab{font-size:10px;letter-spacing:.16em;opacity:.75}.nm{font-size:20px;font-weight:800}.imp{font-size:11px;opacity:.88;margin-top:2px}.at{display:grid;place-items:center;font-weight:800;background:#0a0c10}.pills{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:0 0 12px}.pill{background:#12151c;border:1px solid #232833;border-radius:10px;padding:11px 6px;text-align:center}.pill .k{font-size:9px;color:var(--mute);letter-spacing:.14em;font-weight:700}.pill .v{font-size:15px;font-weight:800;margin-top:4px}.panel{background:#12151c;border:1px solid #232833;border-radius:12px;padding:12px;margin-bottom:10px}.ph{display:flex;justify-content:space-between;margin:2px 0 8px}.ph b{font-size:12px;letter-spacing:.1em;border-left:3px solid var(--pink);padding-left:8px}.ph span{font-size:10px;color:var(--mute)}table{width:100%;border-collapse:collapse}th{text-align:left;font-size:10px;color:var(--mute);padding:6px 4px}th.r,td.r{text-align:right}td{padding:11px 4px;border-top:1px solid #232833}.who{display:flex;gap:10px;align-items:center}.dot{width:22px;height:22px;border-radius:50%;display:grid;place-items:center;font-size:8px;font-weight:800}.pn{font-weight:700}.ps{font-size:11px;color:var(--mute)}.pos{color:var(--good);font-weight:700}.neg{color:var(--bad);font-weight:700}.grade{font-weight:800;color:var(--pink);font-size:16px}.cols{display:grid;grid-template-columns:1fr 1fr;gap:8px}.col h3{font-size:11px;color:var(--mute);margin:0 0 6px}.mrow{display:flex;justify-content:space-between;align-items:center;padding:9px 2px;border-top:1px solid #232833}.badge{min-width:34px;text-align:center;font-weight:800;padding:4px 6px;border-radius:6px}.g{background:#16361f;color:#3DDC97}.y{background:#3a3210;color:#e8c547}.r{background:#3a1518;color:#ff6b6b}.foot{display:flex;justify-content:space-between;color:var(--mute);font-size:11px}.foot b{color:var(--pink)}";
}
function lookCol(title, items) {
  const body = items.map((x) =>
    "<div class=\"mrow\"><div><div class=\"pn\">" + esc(x.player) + "</div><div class=\"ps\">" +
    esc([x.pos, x.note].filter(Boolean).join(" · ")) + "</div></div><div class=\"badge " +
    badgeClass(x.score) + "\">" + esc(x.score) + "</div></div>"
  ).join("") || "<div class=\"ps\">No tagged looks</div>";
  return "<div class=\"col\"><h3>" + esc(title) + "</h3>" + body + "</div>";
}
function sheetHTML(card, g) {
  const rows = propsFor(card, g.id);
  const week = card.week ? ("WEEK " + card.week) : "";
  const ai = g.away_implied != null ? ("IMPLIED " + g.away_implied) : "";
  const hi = g.home_implied != null ? ("IMPLIED " + g.home_implied) : "";
  const pills = [
    ["SPREAD", g.spread || "—"],
    ["TOTAL", g.total != null ? String(g.total) : "—"],
    ["KICKOFF", g.when || "—"],
    ["ROOF", g.roof || "—"]
  ].map((x) => "<div class=\"pill\"><div class=\"k\">" + esc(x[0]) + "</div><div class=\"v\">" + esc(x[1]) + "</div></div>").join("");
  const body = rows.map((p) => {
    const gapCls = Number(p.edge) >= 0 ? "pos" : "neg";
    return "<tr><td><div class=\"who\"><div class=\"dot\" style=\"" + dotStyle(p.team) + "\">" + esc(p.team || "") +
      "</div><div><div class=\"pn\">" + esc(p.player) + "</div><div class=\"ps\">" +
      esc([p.pos, p.market_label || p.market].filter(Boolean).join(" · ")) +
      "</div></div></div></td><td class=\"r\">" + (p.proj != null ? p.proj : "—") +
      "</td><td class=\"r\">" + (p.line != null ? p.line : "—") +
      "</td><td class=\"r " + gapCls + "\">" + fmt(p.edge) +
      "</td><td class=\"r grade\">" + grade(p) + "</td></tr>";
  }).join("") || "<tr><td colspan=\"5\">No props</td></tr>";
  const looks = looksFor(g, rows);
  const homeLooks = looks.filter((x) => x.side === "home" || x.team === g.home);
  const awayLooks = looks.filter((x) => x.side === "away" || x.team === g.away);
  const whenLine = [g.when, g.tv, g.venue].filter(Boolean).join(" · ");
  return "<!DOCTYPE html><html><head><meta charset=\"utf-8\"/><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"/><style>" +
    sheetCSS() + "</style></head><body><div class=\"wrap\"><div class=\"kicker\"><div class=\"kicker-l\"><b>" +
    esc(week) + "</b> NFL · GAME SHEET</div><div class=\"logo\"><span>x</span>DESK</div></div><h1>" +
    esc(nameOf(g.away)) + " AT " + esc(nameOf(g.home)) + "</h1><div class=\"meta\">" + esc(whenLine) +
    "</div><div class=\"teams\"><div style=\"" + sideStyle(g.away, "left") + "\"><div class=\"lab\">AWAY</div><div class=\"nm\">" +
    esc(nameOf(g.away)) + "</div><div class=\"imp\">" + esc(ai) + "</div></div><div class=\"at\">AT</div><div style=\"" +
    sideStyle(g.home, "right") + "\"><div class=\"lab\">HOME</div><div class=\"nm\">" +
    esc(nameOf(g.home)) + "</div><div class=\"imp\">" + esc(hi) + "</div></div></div><div class=\"pills\">" +
    pills + "</div><div class=\"panel\"><div class=\"ph\"><b>PROPS AT A GLANCE</b><span>PROJ VS LINE</span></div><table><thead><tr><th>PLAYER</th><th class=\"r\">PROJ</th><th class=\"r\">LINE</th><th class=\"r\">GAP</th><th class=\"r\">GRADE</th></tr></thead><tbody>" +
    body + "</tbody></table></div><div class=\"panel\"><div class=\"ph\"><b>KEY MATCHUPS</b><span>SCORE 0 TO 100</span></div><div class=\"cols\">" +
    lookCol((g.home || "") + " OFFENSE VS " + (g.away || ""), homeLooks) +
    lookCol((g.away || "") + " OFFENSE VS " + (g.home || ""), awayLooks) +
    "</div></div><div class=\"foot\"><div><b>desk</b> · research</div><div>" +
    esc(card.status || "") + "</div></div></div></body></html>";
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
    row.height = 54;
    row.dismissOnSelect = true;
    row.onSelect = async () => { await presentSheet(card, g); };
    const t = row.addText(nameOf(g.away) + " AT " + nameOf(g.home) + "\n" + [g.when, g.spread, g.total].filter(Boolean).join(" · ") + " · " + n + " props");
    t.titleFont = Font.boldSystemFont(16);
    t.subtitleFont = Font.systemFont(11);
    table.addRow(row);
  }
  await table.present();
}
function buildWidget(card) {
  const w = new ListWidget();
  const games = gamesFrom(card);
  const g = games.find((x) => String(x.when || "").indexOf("FINAL") === -1) || games[0] || {};
  const pal = palette(g.home || g.away);
  w.backgroundColor = new Color(pal[0]);
  w.setPadding(12, 14, 12, 14);
  const p = propsFor(card, g.id)[0];
  const k = w.addText("WEEK " + (card.week || "") + "  ·  GAME SHEET");
  k.font = Font.boldSystemFont(10);
  k.textColor = new Color("#d6dbe6");
  const title = w.addText(nameOf(g.away) + " AT " + nameOf(g.home));
  title.font = Font.boldSystemFont(16);
  title.textColor = Color.white();
  title.minimumScaleFactor = 0.6;
  w.addSpacer(8);
  if (p) {
    const nm = w.addText(p.player);
    nm.font = Font.boldSystemFont(15);
    nm.textColor = Color.white();
    const gap = w.addText((p.proj != null ? p.proj : "—") + " vs " + (p.line != null ? p.line : "—") + "   " + fmt(p.edge));
    gap.font = Font.mediumSystemFont(12);
    gap.textColor = new Color(pal[1]);
  }
  w.addSpacer();
  const f = w.addText("xDESK");
  f.font = Font.boldSystemFont(12);
  f.textColor = new Color("#ff2d7b");
  return w;
}
async function run() {
  let card;
  try { card = await loadCard(); }
  catch (e) {
    if (config.runsInWidget) {
      const w = new ListWidget(); w.addText("Feed failed"); Script.setWidget(w); Script.complete(); return;
    }
    const a = new Alert(); a.title = "NFL Desk feed failed"; a.message = String(e); a.addAction("OK"); await a.present(); Script.complete(); return;
  }
  if (config.runsInWidget) { Script.setWidget(buildWidget(card)); Script.complete(); return; }
  await pickGame(card);
  Script.complete();
}
await run();
