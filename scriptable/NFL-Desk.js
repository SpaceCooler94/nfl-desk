// NFL Desk — Scriptable
// Fetches feed/current.json from GitHub and renders the week card.
//
// Setup:
//   1. Paste this file into Scriptable as "NFL Desk"
//   2. Default repo is public: SpaceCooler94/nfl-desk
//   3. Private repo: Keychain.set("nflDeskGithubToken", "ghp_...")
//
// Widget: add a Scriptable medium widget pointed at this script.

const OWNER = "SpaceCooler94";
const REPO = "nfl-desk";
const BRANCH = "main";
const FEED_PATH = "feed/current.json";
const EDGE_FLAG = 3.0;

function feedUrl() {
  return (
    "https://raw.githubusercontent.com/" +
    OWNER +
    "/" +
    REPO +
    "/" +
    BRANCH +
    "/" +
    FEED_PATH +
    "?t=" +
    Date.now()
  );
}

function apiUrl() {
  return (
    "https://api.github.com/repos/" +
    OWNER +
    "/" +
    REPO +
    "/contents/" +
    FEED_PATH +
    "?ref=" +
    BRANCH
  );
}

function token() {
  try {
    if (Keychain.contains("nflDeskGithubToken")) {
      return Keychain.get("nflDeskGithubToken");
    }
  } catch (e) {}
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

function fmtNum(n, digits) {
  if (n === null || n === undefined || isNaN(n)) return "—";
  const d = digits === undefined ? 1 : digits;
  const v = Number(n);
  return (v > 0 ? "+" : "") + v.toFixed(d);
}

function spreadLabel(g) {
  if (g.market_spread === null || g.market_spread === undefined) {
    return g.away + " @ " + g.home;
  }
  const s = Number(g.market_spread);
  if (s < 0) return g.home + " " + s.toFixed(1);
  if (s > 0) return g.away + " " + (-s).toFixed(1);
  return "PK";
}

function playColor(play) {
  if (play === "HOME" || play === "AWAY") return new Color("#3DDC97");
  if (play === "OVER" || play === "UNDER") return new Color("#5B8DEF");
  return new Color("#8E8E93");
}

function edgeTone(edge) {
  if (edge === null || edge === undefined) return new Color("#8E8E93");
  const a = Math.abs(Number(edge));
  if (a >= EDGE_FLAG) return new Color("#FF9F0A");
  return new Color("#EBEBF5");
}

async function presentTable(card) {
  const table = new UITable();
  table.showSeparators = true;

  const head = new UITableRow();
  head.isHeader = true;
  head.height = 44;
  const title = card.status === "SEED_PRIOR" ? "SEED — do not bet" : "LIVE card";
  head.addText("NFL " + card.season + "  Wk " + card.week + "   " + title);
  table.addRow(head);

  const sub = new UITableRow();
  sub.height = 28;
  sub.addText(card.disclaimer || card.generated_at || "");
  table.addRow(sub);

  for (const g of card.games) {
    const row = new UITableRow();
    row.height = 56;
    row.cellSpacing = 8;
    row.onSelect = () => showGame(card, g);

    const left = row.addText(g.when + "\n" + g.away + " @ " + g.home);
    left.widthWeight = 35;
    left.titleFont = Font.mediumSystemFont(14);
    left.subtitleFont = Font.systemFont(11);

    const mid = row.addText(spreadLabel(g) + "\nTot " + (g.market_total ?? "—"));
    mid.widthWeight = 25;
    mid.titleFont = Font.mediumSystemFont(14);

    const edgeStr =
      "m " +
      fmtNum(g.model_spread) +
      "\nΔ " +
      fmtNum(g.edge_spread);
    const right = row.addText(edgeStr);
    right.widthWeight = 20;
    right.titleColor = edgeTone(g.edge_spread);

    const badge = row.addText(g.play || "PASS");
    badge.widthWeight = 15;
    badge.titleColor = playColor(g.play);
    badge.titleFont = Font.boldSystemFont(13);

    table.addRow(row);
  }

  await table.present();
}

async function showGame(card, g) {
  const a = new Alert();
  a.title = g.away + " @ " + g.home;
  a.message = [
    g.when + (g.tv ? "  " + g.tv : ""),
    "Market: " + spreadLabel(g) + "  O/U " + (g.market_total ?? "—"),
    "Model spread: " + fmtNum(g.model_spread) + " (home margin)",
    "Model total: " + fmtNum(g.model_total),
    "Home WP: " + (g.home_wp != null ? (100 * g.home_wp).toFixed(0) + "%" : "—"),
    "Edge spread: " + fmtNum(g.edge_spread),
    "Play: " + g.play + "   Units: " + (g.units ?? 0),
    "",
    g.note || "No note",
    "",
    "Card status: " + card.status
  ].join("\n");
  a.addAction("OK");
  await a.present();
}

function nextGame(card) {
  const now = Date.now();
  const upcoming = card.games
    .filter((g) => g.kickoff && Date.parse(g.kickoff) >= now - 3 * 3600 * 1000)
    .sort((a, b) => Date.parse(a.kickoff) - Date.parse(b.kickoff));
  return upcoming[0] || card.games[0];
}

function buildWidget(card) {
  const w = new ListWidget();
  w.backgroundColor = new Color("#0B0F14");
  w.setPadding(12, 14, 12, 14);

  const kicker = w.addText("NFL DESK  ·  W" + card.week);
  kicker.font = Font.boldSystemFont(10);
  kicker.textColor = new Color("#8E8E93");

  const banner = w.addText(card.status === "SEED_PRIOR" ? "SEED CARD" : "LIVE");
  banner.font = Font.boldSystemFont(16);
  banner.textColor =
    card.status === "SEED_PRIOR" ? new Color("#FF9F0A") : new Color("#3DDC97");

  w.addSpacer(6);

  const g = nextGame(card);
  const match = w.addText(g.away + " @ " + g.home);
  match.font = Font.boldSystemFont(18);
  match.textColor = Color.white();

  const line = w.addText(g.when + "   " + spreadLabel(g));
  line.font = Font.systemFont(12);
  line.textColor = new Color("#EBEBF5");

  const edge = w.addText(
    "Model " + fmtNum(g.model_spread) + "   Δ " + fmtNum(g.edge_spread) + "   " + g.play
  );
  edge.font = Font.mediumSystemFont(12);
  edge.textColor = playColor(g.play);

  w.addSpacer();
  const foot = w.addText((card.generated_at || "").replace("T", " ").slice(0, 16) + "Z");
  foot.font = Font.systemFont(9);
  foot.textColor = new Color("#636366");
  return w;
}

async function run() {
  let card;
  try {
    card = await loadCard();
  } catch (e) {
    if (config.runsInWidget) {
      const w = new ListWidget();
      w.addText("Feed failed");
      w.addText(String(e));
      Script.setWidget(w);
      Script.complete();
      return;
    }
    const a = new Alert();
    a.title = "NFL Desk feed failed";
    a.message = String(e);
    a.addAction("OK");
    await a.present();
    Script.complete();
    return;
  }

  if (config.runsInWidget) {
    Script.setWidget(buildWidget(card));
    Script.complete();
    return;
  }

  await presentTable(card);
  Script.complete();
}

await run();
