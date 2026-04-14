// BID — Accesibilidad Escolar LAC
// Presentación para revisión del primer indicador geoespacial
// Run: NODE_PATH=/usr/local/lib/node_modules_global/lib/node_modules node ppt_bid.js

const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.title = "Accesibilidad Escolar en América Latina y el Caribe";
pres.author = "Angela Lopez Sanchez";

// ── Color palette (BID-aligned) ──
const C = {
  navy:       "00284E",
  navyMid:    "003F7F",
  blue:       "0077C8",
  blueMid:    "0093D7",
  blueLight:  "E6F2FB",
  gold:       "F4A726",
  goldDark:   "C47F00",
  white:      "FFFFFF",
  offWhite:   "F7FAFD",
  textDark:   "1A2B4A",
  textMid:    "3D5A80",
  textLight:  "6B7F9E",
  separator:  "D0E4F5",
  green:      "1E7F5C",
  greenLight: "E8F7F1",
  orange:     "E07B2A",
  orangeLight:"FDF0E4",
  red:        "C0392B",
  redLight:   "FBEAEA",
  goldLight:  "FFF8E8",
};

// ── Shared helpers ──
function addFrame(slide, title, opts = {}) {
  const bg = opts.bg || C.white;
  slide.background = { color: bg };
  // Left accent bar
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 0.12, h: 5.625,
    fill: { color: C.navy }, line: { color: C.navy }
  });
  // Top accent bar
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.12, y: 0, w: 9.88, h: 0.06,
    fill: { color: C.blue }, line: { color: C.blue }
  });
  if (title) {
    slide.addText(title.toUpperCase(), {
      x: 0.28, y: 0.12, w: 9.3, h: 0.55,
      fontSize: 13, fontFace: "Calibri", bold: true,
      color: C.navy, charSpacing: 1.5, margin: 0
    });
    // Title underline
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 0.28, y: 0.64, w: 9.3, h: 0.025,
      fill: { color: C.separator }, line: { color: C.separator }
    });
  }
  // Footer
  slide.addText("BID — Plataforma de Indicadores Geoespaciales de Educación — LAC 2025/26", {
    x: 0.28, y: 5.3, w: 8.6, h: 0.25,
    fontSize: 7.5, fontFace: "Calibri", color: C.textLight, margin: 0
  });
}

function statCard(slide, x, y, w, h, value, label, sub, color) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h,
    fill: { color: C.white }, line: { color: C.separator, pt: 1 },
    shadow: { type: "outer", blur: 6, offset: 2, angle: 135, color: C.navy, opacity: 0.07 }
  });
  // Top accent
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h: 0.07,
    fill: { color: color || C.blue }, line: { color: color || C.blue }
  });
  slide.addText(value, {
    x: x + 0.15, y: y + 0.14, w: w - 0.3, h: 0.7,
    fontSize: 36, fontFace: "Calibri", bold: true,
    color: color || C.blue, align: "center", margin: 0
  });
  slide.addText(label, {
    x: x + 0.1, y: y + 0.82, w: w - 0.2, h: 0.32,
    fontSize: 10.5, fontFace: "Calibri", bold: true,
    color: C.textDark, align: "center", margin: 0
  });
  if (sub) {
    slide.addText(sub, {
      x: x + 0.1, y: y + 1.1, w: w - 0.2, h: 0.28,
      fontSize: 8.5, fontFace: "Calibri", color: C.textLight, align: "center", margin: 0
    });
  }
}

// ═══════════════════════════════════════
// S1 — PORTADA
// ═══════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.navy };

  // Left color stripe
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 0.55, h: 5.625,
    fill: { color: C.blue }, line: { color: C.blue }
  });
  // Gold accent bottom bar
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 5.1, w: 10, h: 0.07,
    fill: { color: C.gold }, line: { color: C.gold }
  });

  // Badge
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.85, y: 0.5, w: 3.6, h: 0.38,
    fill: { color: C.gold }, line: { color: C.gold }
  });
  s.addText("FASE 1 — PRIMER INDICADOR GEOESPACIAL", {
    x: 0.85, y: 0.5, w: 3.6, h: 0.38,
    fontSize: 8, fontFace: "Calibri", bold: true,
    color: C.navy, align: "center", valign: "middle", margin: 0
  });

  // Title
  s.addText("Accesibilidad Escolar en\nAmérica Latina y el Caribe", {
    x: 0.75, y: 1.05, w: 8.8, h: 1.6,
    fontSize: 34, fontFace: "Calibri", bold: true,
    color: C.white, align: "left", valign: "top", margin: 0
  });

  // Subtitle
  s.addText("Evaluación de cobertura, calidad georreferencial\ny marco de referencia sectorial — 21 países", {
    x: 0.75, y: 2.7, w: 7.5, h: 0.95,
    fontSize: 15, fontFace: "Calibri",
    color: "A8C9E8", align: "left", margin: 0
  });

  // Divider line
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.75, y: 3.72, w: 5.5, h: 0.04,
    fill: { color: C.gold }, line: { color: C.gold }
  });

  // Details
  s.addText([
    { text: "Preparado para: ", options: { bold: true } },
    { text: "Banco Interamericano de Desarrollo (BID)", options: {} }
  ], {
    x: 0.75, y: 3.84, w: 8, h: 0.28,
    fontSize: 10.5, fontFace: "Calibri", color: "A8C9E8", margin: 0
  });
  s.addText([
    { text: "Fecha: ", options: { bold: true } },
    { text: "Marzo 2026", options: {} }
  ], {
    x: 0.75, y: 4.13, w: 8, h: 0.28,
    fontSize: 10.5, fontFace: "Calibri", color: "A8C9E8", margin: 0
  });
  s.addText([
    { text: "Alcance: ", options: { bold: true } },
    { text: "21 países, preescolar–educación media, sector público/privado", options: {} }
  ], {
    x: 0.75, y: 4.41, w: 8.5, h: 0.28,
    fontSize: 10.5, fontFace: "Calibri", color: "A8C9E8", margin: 0
  });
}

// ═══════════════════════════════════════
// S2 — RESUMEN EJECUTIVO
// ═══════════════════════════════════════
{
  const s = pres.addSlide();
  addFrame(s, "Resumen Ejecutivo");

  s.addText("¿Dónde estamos hoy?", {
    x: 0.28, y: 0.75, w: 9.3, h: 0.38,
    fontSize: 17, fontFace: "Calibri", bold: true, color: C.navy, margin: 0
  });

  // 3 stat cards
  statCard(s, 0.28,  1.2, 2.9, 1.55, "604,089", "escuelas en la base",          "21 países de LAC", C.blue);
  statCard(s, 3.48,  1.2, 2.9, 1.55, "80.6%",   "cobertura vs. universo público","503k / 623k escuelas públicas", C.navyMid);
  statCard(s, 6.68,  1.2, 2.9, 1.55, "96.5%",   "con coordenadas válidas",      "583k / 604k geocodificadas", C.green);

  // Context paragraph
  s.addText("Todos los conteos provienen directamente de registros ministeriales crudos, aplicando los mismos filtros del pipeline de la plataforma. Las diferencias con marcos oficiales publicados son menores al 5% en 10 de 21 países.", {
    x: 0.28, y: 2.85, w: 9.3, h: 0.55,
    fontSize: 10.5, fontFace: "Calibri", color: C.textMid, margin: 0
  });

  // Two key flags
  const flagData = [
    { color: C.orange, bg: C.orangeLight, icon: "⚠", txt: "2 decisiones pendientes para BID antes del cálculo del primer indicador: (1) ¿incluir escuelas privadas? y (2) ¿geocodificar registros faltantes antes del 31 de marzo?" },
    { color: C.blue,   bg: C.blueLight,   icon: "✓", txt: "El piloto de Panamá está completo con 3,617 escuelas y 4 escenarios de accesibilidad (Census × WorldPop × Google/OSM). Listo para la reunión BID." },
  ];
  flagData.forEach((f, i) => {
    const fy = 3.5 + i * 0.77;
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.28, y: fy, w: 9.3, h: 0.65,
      fill: { color: f.bg }, line: { color: f.color, pt: 1 }
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.28, y: fy, w: 0.06, h: 0.65,
      fill: { color: f.color }, line: { color: f.color }
    });
    s.addText(f.txt, {
      x: 0.45, y: fy + 0.05, w: 9.0, h: 0.55,
      fontSize: 9.5, fontFace: "Calibri", color: C.textDark, margin: 0
    });
  });
}

// ═══════════════════════════════════════
// S3 — METODOLOGÍA Y FUENTES
// ═══════════════════════════════════════
{
  const s = pres.addSlide();
  addFrame(s, "Metodología: ¿Cómo construimos la base?");

  s.addText("Todos los conteos son trazables hasta el archivo crudo del ministerio", {
    x: 0.28, y: 0.75, w: 9.3, h: 0.32,
    fontSize: 11, fontFace: "Calibri", color: C.textMid, italic: true, margin: 0
  });

  const steps = [
    { num: "1", title: "Fuente",     body: "Registros administrativos oficiales de cada ministerio de educación (21 países). Archivos crudos almacenados en el repositorio de la plataforma.", color: C.blue },
    { num: "2", title: "Filtros",    body: "Se aplican los mismos filtros del pipeline de producción: subsistema regular, estado activo, nivel K-12. Los filtros de sector varían por país (ver S5).", color: C.navyMid },
    { num: "3", title: "Universo",   body: "Se define el universo de referencia por país: total de escuelas en el archivo crudo (post-filtro). Se distingue público vs. privado donde el archivo lo permite.", color: C.blue },
    { num: "4", title: "Cobertura",  body: "Se calcula cobertura = escuelas en base procesada / universo crudo. Una cobertura >100% indica diferencia en unidad de conteo (ej. PER: cod_mod vs. locales ESCALE).", color: C.navyMid },
  ];

  steps.forEach((st, i) => {
    const col = i % 2 === 0 ? 0.28 : 5.1;
    const row = Math.floor(i / 2);
    const bx = col, by = 1.2 + row * 1.75, bw = 4.5, bh = 1.6;

    s.addShape(pres.shapes.RECTANGLE, {
      x: bx, y: by, w: bw, h: bh,
      fill: { color: C.offWhite }, line: { color: C.separator, pt: 1 }
    });
    // Number badge
    s.addShape(pres.shapes.RECTANGLE, {
      x: bx, y: by, w: 0.42, h: bh,
      fill: { color: st.color }, line: { color: st.color }
    });
    s.addText(st.num, {
      x: bx, y: by, w: 0.42, h: bh,
      fontSize: 18, fontFace: "Calibri", bold: true,
      color: C.white, align: "center", valign: "middle", margin: 0
    });
    s.addText(st.title, {
      x: bx + 0.52, y: by + 0.12, w: bw - 0.62, h: 0.32,
      fontSize: 11.5, fontFace: "Calibri", bold: true, color: C.navy, margin: 0
    });
    s.addText(st.body, {
      x: bx + 0.52, y: by + 0.42, w: bw - 0.62, h: 1.08,
      fontSize: 9.5, fontFace: "Calibri", color: C.textDark, margin: 0
    });
  });

  // Scope note
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.28, y: 4.78, w: 9.3, h: 0.42,
    fill: { color: C.blueLight }, line: { color: C.blue, pt: 1 }
  });
  s.addText("Alcance geográfico: ARG, BHS, BLZ, BOL, BRA, BRB, CHL, COL, CRI, DOM, ECU, GTM, GUY, HND, HTI, JAM, MEX, PAN, PER, PRY, SLV, SUR, URY  |  Países excluidos de gráficos: HTI (sin datos procesados), BHS (solo 77 POIs OSM)", {
    x: 0.38, y: 4.84, w: 9.1, h: 0.32,
    fontSize: 8, fontFace: "Calibri", color: C.textMid, margin: 0
  });
}

// ═══════════════════════════════════════
// S4 — COBERTURA POR PAÍS
// ═══════════════════════════════════════
{
  const s = pres.addSlide();
  addFrame(s, "Cobertura por País: Base vs. Universo Público Oficial");

  // Country data: [iso, label, n_georef, total_universe_est, public_universe, pct_vs_public, confidence]
  // Source: school_coverage_assessment.csv
  const countries = [
    ["MEX", "México",        205848, 243842, 209629,  98.2, "alta"],
    ["BRA", "Brasil",        116542, 180230, 137914,  84.6, "alta"],
    ["ARG", "Argentina",      34167,  45000,  33945, 100.7, "alta"],
    ["COL", "Colombia",       43259,  50866,  42846, 101.0, "alta"],
    ["PER", "Perú",           69142,  88019,  65266, 100.0, "media"],
    ["GTM", "Guatemala",      35973,  35501,  35497, 101.3, "alta"],
    ["CHL", "Chile",           7895,  16659,   7895, 100.0, "media"],
    ["HND", "Honduras",       16234,  17428,  17428,  93.2, "alta"],
    ["ECU", "Ecuador",         6357,  15706,  12767,  49.8, "alta"],
    ["BOL", "Bolivia",        15301,  16159,  15329,  99.8, "alta"],
    ["DOM", "R. Dominicana",   6294,  10615,   7893,  79.7, "alta"],
    ["PRY", "Paraguay",        7900,   8847,   8241,  95.8, "alta"],
    ["SLV", "El Salvador",     5093,   6026,   5143,  99.0, "media"],
    ["CRI", "Costa Rica",      4381,   5268,   4504,  97.2, "alta"],
    ["PAN", "Panamá",          3107,   3660,   3092, 100.5, "alta"],
    ["URY", "Uruguay",         2597,   2597,   2597, 100.0, "alta"],
    ["BLZ", "Belice",           303,    303,    303, 100.0, "alta"],
    ["GUY", "Guyana",           874,    874,    874, 100.0, "media"],
    ["JAM", "Jamaica",          953,    955,    955,  99.8, "media"],
    ["SUR", "Surinam",          547,    958,    953,  57.4, "media"],
    ["BRB", "Barbados",         106,    106,    106, 100.0, "baja"],
  ];

  const sorted = countries.slice().sort((a, b) => b[2] - a[2]).slice(0, 18);

  const chartLabels = sorted.map(c => c[1]);
  const chartValues = sorted.map(c => Math.round(c[2] / 1000 * 10) / 10);

  s.addChart(pres.charts.BAR, [
    { name: "Escuelas con coordenadas (miles)", labels: chartLabels, values: chartValues }
  ], {
    x: 0.22, y: 0.77, w: 5.8, h: 4.55,
    barDir: "bar",
    barGapWidthPct: 45,
    chartColors: ["0077C8"],
    chartArea: { fill: { color: C.white }, roundedCorners: false },
    plotArea: { fill: { color: C.white } },
    catAxisLabelColor: C.textDark, catAxisLabelFontSize: 8.5, catAxisLabelFontFace: "Calibri",
    valAxisLabelColor: C.textLight, valAxisLabelFontSize: 8, valAxisLabelFontFace: "Calibri",
    valGridLine: { color: "E8EEF4", size: 0.5 },
    catGridLine: { style: "none" },
    showValue: true,
    dataLabelPosition: "outEnd",
    dataLabelFontSize: 8,
    dataLabelColor: C.textMid,
    showLegend: false,
    showTitle: false,
  });

  s.addText("Escuelas geocodificadas (miles)", {
    x: 0.22, y: 5.2, w: 5.8, h: 0.2,
    fontSize: 8, fontFace: "Calibri", color: C.textLight, align: "center", margin: 0
  });

  // ── Right side: cobertura vs. marco público ──
  s.addShape(pres.shapes.RECTANGLE, {
    x: 6.25, y: 0.77, w: 3.45, h: 0.38,
    fill: { color: C.navy }, line: { color: C.navy }
  });
  s.addText("País  |  Cobertura vs. Público", {
    x: 6.25, y: 0.77, w: 3.45, h: 0.38,
    fontSize: 8.5, fontFace: "Calibri", bold: true,
    color: C.white, align: "center", valign: "middle", margin: 0
  });

  const tableRows = sorted.map(c => {
    const pct = c[5];
    let col = C.green;
    if (pct < 80) col = C.red;
    else if (pct < 95) col = C.orange;
    return { iso: c[0], name: c[1], pct, col };
  });

  const rowH = 0.245;
  tableRows.forEach((r, i) => {
    const ry = 1.15 + i * rowH;
    if (ry > 5.05) return;
    const bg = i % 2 === 0 ? C.white : C.offWhite;
    s.addShape(pres.shapes.RECTANGLE, {
      x: 6.25, y: ry, w: 3.45, h: rowH,
      fill: { color: bg }, line: { color: C.separator, pt: 0.5 }
    });
    s.addText(r.iso, {
      x: 6.28, y: ry + 0.04, w: 0.5, h: rowH - 0.06,
      fontSize: 8, fontFace: "Calibri", bold: true, color: C.navy, margin: 0
    });
    s.addText(r.name, {
      x: 6.80, y: ry + 0.04, w: 1.8, h: rowH - 0.06,
      fontSize: 8, fontFace: "Calibri", color: C.textDark, margin: 0
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: 8.62, y: ry + 0.06, w: 0.9, h: rowH - 0.12,
      fill: { color: r.col, transparency: 75 }, line: { color: r.col, pt: 0.5 }
    });
    s.addText(r.pct.toFixed(0) + "%", {
      x: 8.62, y: ry + 0.04, w: 0.9, h: rowH - 0.06,
      fontSize: 7.5, fontFace: "Calibri", bold: true, color: r.col, align: "center", margin: 0
    });
  });

  // Legend
  const legendItems = [
    { color: C.green,  label: "≥ 95% — cobertura alta" },
    { color: C.orange, label: "80–94% — cobertura media" },
    { color: C.red,    label: "< 80% — cobertura baja / revisar" },
  ];
  legendItems.forEach((li, i) => {
    const lx = 0.28 + i * 3.1, ly = 5.22;
    s.addShape(pres.shapes.RECTANGLE, {
      x: lx, y: ly, w: 0.18, h: 0.16,
      fill: { color: li.color }, line: { color: li.color }
    });
    s.addText(li.label, {
      x: lx + 0.22, y: ly, w: 2.7, h: 0.18,
      fontSize: 7.5, fontFace: "Calibri", color: C.textMid, margin: 0
    });
  });
}

// ═══════════════════════════════════════
// S5 — COMPOSICIÓN SECTORIAL DE LA BASE
// ═══════════════════════════════════════
{
  const s = pres.addSlide();
  addFrame(s, "Composición Sectorial: ¿Qué incluye la base actual?");

  s.addText("La base no es homogénea — el alcance sectorial varía por país según el archivo del ministerio y los filtros del script R.", {
    x: 0.28, y: 0.76, w: 9.3, h: 0.32,
    fontSize: 10, fontFace: "Calibri", color: C.textMid, italic: true, margin: 0
  });

  const categories = [
    {
      color: C.blue, label: "Solo público / oficial",
      countries: "ARG, BOL, BRA, COL, CRI, ECU, MEX, PAN, URY",
      count: "9 países",
      note: "Filtra explícitamente a sector estatal. Escuelas privadas no incluidas."
    },
    {
      color: C.navyMid, label: "Público + mixto (subvencionado)",
      countries: "DOM, PRY, GTM",
      count: "3 países",
      note: "Incluye escuelas privadas subvencionadas, cooperativas o semioficiales."
    },
    {
      color: C.orange, label: "Incluye privadas (accidental o intencional)",
      countries: "SLV (filtro comentado), CHL (incluye pagado)",
      count: "2 países",
      note: "SLV: el filtro de sector está comentado en el script — ~883 privadas incluidas sin intención. CHL: excluye Corp. Delegada pero retiene particular pagado (cod_depe 3)."
    },
    {
      color: C.textLight, label: "Sin archivo crudo con privadas",
      countries: "BHS, BLZ, BRB, GUY, HND, HTI, JAM, SUR",
      count: "8 países",
      note: "El archivo ministerial disponible solo contiene escuelas públicas/gubernamentales. No es posible incorporar privadas sin fuente adicional."
    },
  ];

  categories.forEach((cat, i) => {
    const by = 1.18 + i * 0.97;
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.28, y: by, w: 9.3, h: 0.87,
      fill: { color: C.offWhite }, line: { color: C.separator, pt: 1 }
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.28, y: by, w: 0.07, h: 0.87,
      fill: { color: cat.color }, line: { color: cat.color }
    });
    // Badge
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.44, y: by + 0.1, w: 0.78, h: 0.24,
      fill: { color: cat.color }, line: { color: cat.color }
    });
    s.addText(cat.count, {
      x: 0.44, y: by + 0.1, w: 0.78, h: 0.24,
      fontSize: 8, fontFace: "Calibri", bold: true,
      color: C.white, align: "center", valign: "middle", margin: 0
    });
    s.addText(cat.label, {
      x: 1.32, y: by + 0.08, w: 4.2, h: 0.28,
      fontSize: 11, fontFace: "Calibri", bold: true, color: C.navy, margin: 0
    });
    s.addText(cat.countries, {
      x: 1.32, y: by + 0.34, w: 4.2, h: 0.22,
      fontSize: 9, fontFace: "Calibri", bold: true, color: cat.color, margin: 0
    });
    s.addText(cat.note, {
      x: 5.65, y: by + 0.1, w: 3.8, h: 0.67,
      fontSize: 9, fontFace: "Calibri", color: C.textMid, margin: 0
    });
  });

  // Bottom note
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.28, y: 5.05, w: 9.3, h: 0.35,
    fill: { color: C.blueLight }, line: { color: C.blue, pt: 1 }
  });
  s.addText("Nota: La inconsistencia sectorial afecta la comparabilidad entre países. Recomendación: estandarizar la definición antes del cálculo del indicador (ver decisión en S6).", {
    x: 0.38, y: 5.1, w: 9.1, h: 0.27,
    fontSize: 8.5, fontFace: "Calibri", color: C.navyMid, margin: 0
  });
}

// ═══════════════════════════════════════
// S6 — DECISIÓN 1: ¿INCLUIR PRIVADAS?
// ═══════════════════════════════════════
{
  const s = pres.addSlide();
  addFrame(s, "Decisión 1: ¿Incluir Escuelas Privadas en el Indicador?");

  // Decision banner (navy bg, gold accent left + right stripes)
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.28, y: 0.75, w: 9.3, h: 0.45,
    fill: { color: C.navy }, line: { color: C.navy }
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.28, y: 0.75, w: 0.25, h: 0.45,
    fill: { color: C.gold }, line: { color: C.gold }
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 9.33, y: 0.75, w: 0.25, h: 0.45,
    fill: { color: C.gold }, line: { color: C.gold }
  });
  s.addText("DECISIÓN REQUERIDA ANTES DEL CÁLCULO DEL INDICADOR — REUNIÓN BID", {
    x: 0.55, y: 0.75, w: 8.75, h: 0.45,
    fontSize: 10, fontFace: "Calibri", bold: true,
    color: C.white, align: "center", valign: "middle", margin: 0
  });

  // Evidence box
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.28, y: 1.3, w: 4.55, h: 2.45,
    fill: { color: C.offWhite }, line: { color: C.separator, pt: 1 }
  });
  s.addText("Evidencia: asistencia a escuelas públicas por quintil de ingreso (LAC)", {
    x: 0.38, y: 1.37, w: 4.35, h: 0.32,
    fontSize: 9.5, fontFace: "Calibri", bold: true, color: C.navy, margin: 0
  });

  const quintiles = [
    { label: "Q1 (más pobre)", pct: 90.4, color: C.blue },
    { label: "Q2",             pct: 82.1, color: C.blue },
    { label: "Q3",             pct: 73.5, color: C.blueMid },
    { label: "Q4",             pct: 62.8, color: C.orange },
    { label: "Q5 (más rico)",  pct: 49.5, color: C.red },
  ];
  quintiles.forEach((q, i) => {
    const qy = 1.78 + i * 0.34;
    const barW = (q.pct / 100) * 3.0;
    s.addText(q.label, {
      x: 0.38, y: qy, w: 1.4, h: 0.28,
      fontSize: 8.5, fontFace: "Calibri", color: C.textDark, margin: 0
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: 1.85, y: qy + 0.04, w: barW, h: 0.2,
      fill: { color: q.color }, line: { color: q.color }
    });
    s.addText(q.pct + "%", {
      x: 1.85 + barW + 0.05, y: qy + 0.02, w: 0.5, h: 0.24,
      fontSize: 8.5, fontFace: "Calibri", bold: true, color: q.color, margin: 0
    });
  });
  s.addText("Fuente: BID, AsisPubHHSS — Tasa de asistencia a escuelas públicas, LAC promedio", {
    x: 0.38, y: 3.62, w: 4.35, h: 0.2,
    fontSize: 7, fontFace: "Calibri", color: C.textLight, italic: true, margin: 0
  });

  // Right side: implications
  s.addShape(pres.shapes.RECTANGLE, {
    x: 5.05, y: 1.3, w: 4.5, h: 2.45,
    fill: { color: C.offWhite }, line: { color: C.separator, pt: 1 }
  });
  s.addText("Implicaciones para el indicador", {
    x: 5.15, y: 1.37, w: 4.3, h: 0.32,
    fontSize: 9.5, fontFace: "Calibri", bold: true, color: C.navy, margin: 0
  });

  const points = [
    { icon: "→", text: "Solo 49.5% del quintil más rico asiste a escuela pública en LAC. Excluir privadas subestimaría el acceso en zonas urbanas ricas." },
    { icon: "→", text: "En BRA Q5 = 28.7%, COL Q5 = 29.8%. El sesgo es crítico para análisis de equidad urbana." },
    { icon: "→", text: "Gap de georef de privadas: mínimo en archivos disponibles (–1 a –4 pp). La calidad georreferencial es comparable a públicas." },
    { icon: "⚠", text: "PAN: Anexo 2 no incluye coordenadas de 525 particulares. Requiere geocodificación adicional si se incluyen." },
  ];
  points.forEach((p, i) => {
    const py = 1.77 + i * 0.44;
    s.addText(p.icon, {
      x: 5.15, y: py, w: 0.22, h: 0.38,
      fontSize: 10, fontFace: "Calibri", bold: true,
      color: i < 3 ? C.blue : C.orange, margin: 0
    });
    s.addText(p.text, {
      x: 5.38, y: py, w: 4.05, h: 0.38,
      fontSize: 8.5, fontFace: "Calibri", color: C.textDark, margin: 0
    });
  });

  // Options comparison
  const options = [
    { label: "Opción A: Solo públicas",   pros: "Mayor consistencia, ya disponible", cons: "Subestima acceso en Q4–Q5; sesgo en zonas urbanas; CHL/SLV requieren corrección", color: C.orange },
    { label: "Opción B: Público + privado", pros: "Refleja acceso real; consistente con evidencia de quintiles; PAN requiere geocodificación adicional (~525 escuelas)", cons: "Requiere estandarizar 8 países sin datos privados; trabajo adicional antes del 31", color: C.green },
  ];
  options.forEach((opt, i) => {
    const ox = 0.28 + i * 4.78, oy = 3.88;
    s.addShape(pres.shapes.RECTANGLE, {
      x: ox, y: oy, w: 4.55, h: 1.1,
      fill: { color: C.white }, line: { color: opt.color, pt: 1.5 }
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: ox, y: oy, w: 4.55, h: 0.34,
      fill: { color: opt.color }, line: { color: opt.color }
    });
    s.addText(opt.label, {
      x: ox + 0.1, y: oy, w: 4.35, h: 0.34,
      fontSize: 10, fontFace: "Calibri", bold: true,
      color: C.white, valign: "middle", margin: 0
    });
    s.addText([
      { text: "✓ ", options: { bold: true, color: C.green } },
      { text: opt.pros + "\n", options: { color: C.textDark } },
      { text: "✗ ", options: { bold: true, color: C.red } },
      { text: opt.cons, options: { color: C.textDark } },
    ], {
      x: ox + 0.1, y: oy + 0.38, w: 4.35, h: 0.68,
      fontSize: 8.5, fontFace: "Calibri", margin: 0
    });
  });
}

// ═══════════════════════════════════════
// S7 — GEORREFERENCIACIÓN: 3 CAPAS
// ═══════════════════════════════════════
{
  const s = pres.addSlide();
  addFrame(s, "Calidad Georreferencial: Tres Niveles de Cobertura");

  // Cascade boxes
  const cascade = [
    { val: "~750,000", label: "Universo oficial LAC", sub: "Estimado total de escuelas K-12 en 21 países\n(público + privado)", color: C.textLight, bg: "F0F4F8" },
    { val: "604,089",  label: "En la base procesada", sub: "Registros coincidentes en el pipeline\n80.6% del universo público", color: C.blue, bg: C.blueLight },
    { val: "583,256",  label: "Con coordenadas válidas", sub: "96.5% de la base procesada\nListas para el análisis de accesibilidad", color: C.green, bg: C.greenLight },
  ];

  cascade.forEach((c, i) => {
    const cx = 0.48 + i * 3.18, cy = 0.9;
    // Box
    s.addShape(pres.shapes.RECTANGLE, {
      x: cx, y: cy, w: 2.8, h: 1.55,
      fill: { color: c.bg }, line: { color: c.color, pt: 1.5 }
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: cx, y: cy, w: 2.8, h: 0.07,
      fill: { color: c.color }, line: { color: c.color }
    });
    s.addText(c.val, {
      x: cx + 0.1, y: cy + 0.12, w: 2.6, h: 0.62,
      fontSize: 26, fontFace: "Calibri", bold: true,
      color: c.color, align: "center", margin: 0
    });
    s.addText(c.label, {
      x: cx + 0.1, y: cy + 0.72, w: 2.6, h: 0.28,
      fontSize: 9.5, fontFace: "Calibri", bold: true,
      color: C.navy, align: "center", margin: 0
    });
    s.addText(c.sub, {
      x: cx + 0.1, y: cy + 0.98, w: 2.6, h: 0.5,
      fontSize: 8, fontFace: "Calibri", color: C.textMid, align: "center", margin: 0
    });
    // Arrow
    if (i < 2) {
      s.addShape(pres.shapes.RECTANGLE, {
        x: cx + 2.82, y: cy + 0.73, w: 0.28, h: 0.06,
        fill: { color: C.textLight }, line: { color: C.textLight }
      });
      s.addText("▶", {
        x: cx + 3.0, y: cy + 0.67, w: 0.2, h: 0.18,
        fontSize: 9, fontFace: "Calibri", color: C.textLight, margin: 0
      });
    }
  });

  // Breakdown by coord source (Panama example extended)
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.28, y: 2.65, w: 9.3, h: 0.35,
    fill: { color: C.navy }, line: { color: C.navy }
  });
  s.addText("Jerarquía de fuente de coordenadas (ejemplo: Panamá, piloto del indicador)", {
    x: 0.38, y: 2.65, w: 9.1, h: 0.35,
    fontSize: 9.5, fontFace: "Calibri", bold: true,
    color: C.white, valign: "middle", margin: 0
  });

  const sources = [
    { level: "Nivel 1", name: "GPS de campo (Anexo 2 MEDUCA)", n: "3,070 escuelas", pct: "84.9%", acc: "Alta", color: C.green },
    { level: "Nivel 2", name: "Centroide de corregimiento", n: "545 escuelas", pct: "15.1%", acc: "Media (~2-4 min sesgo)", color: C.orange },
    { level: "Nivel 3", name: "Centroide de distrito", n: "2 escuelas", pct: "0.06%", acc: "Baja (uso excepcional)", color: C.red },
  ];

  const colW = [1.2, 3.5, 1.4, 1.0, 1.5, 0.8];
  const colX = [0.28, 1.52, 5.06, 6.5, 7.54, 9.08];
  const headers = ["Nivel", "Fuente de Coordenadas", "N Escuelas", "% Total", "Precisión", ""];
  headers.forEach((h, j) => {
    s.addShape(pres.shapes.RECTANGLE, {
      x: colX[j], y: 3.02, w: colW[j], h: 0.3,
      fill: { color: C.blueLight }, line: { color: C.separator, pt: 0.5 }
    });
    s.addText(h, {
      x: colX[j] + 0.05, y: 3.02, w: colW[j] - 0.05, h: 0.3,
      fontSize: 8.5, fontFace: "Calibri", bold: true, color: C.navy,
      valign: "middle", margin: 0
    });
  });

  sources.forEach((r, i) => {
    const ry = 3.33 + i * 0.38;
    const rowBg = i % 2 === 0 ? C.white : C.offWhite;
    const rowData = [r.level, r.name, r.n, r.pct, r.acc];
    rowData.forEach((d, j) => {
      s.addShape(pres.shapes.RECTANGLE, {
        x: colX[j], y: ry, w: colW[j], h: 0.36,
        fill: { color: rowBg }, line: { color: C.separator, pt: 0.5 }
      });
      s.addText(d, {
        x: colX[j] + 0.05, y: ry + 0.05, w: colW[j] - 0.1, h: 0.26,
        fontSize: 8.5, fontFace: "Calibri",
        color: j === 0 ? r.color : C.textDark, bold: j === 0, margin: 0
      });
    });
    // Color dot in last column
    s.addShape(pres.shapes.OVAL, {
      x: colX[5] + 0.25, y: ry + 0.1, w: 0.18, h: 0.18,
      fill: { color: r.color }, line: { color: r.color }
    });
  });

  // Note on centroid bias
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.28, y: 4.52, w: 9.3, h: 0.6,
    fill: { color: C.orangeLight }, line: { color: C.orange, pt: 1 }
  });
  s.addText([
    { text: "Sesgo del centroide: ", options: { bold: true } },
    { text: "Las 545 escuelas con centroide de corregimiento en Panamá introducen un sesgo de ~2-4 minutos en el tiempo de viaje calculado. Son mayoritariamente escuelas ", options: {} },
    { text: "particulares (519 de 525)", options: { bold: true, color: C.orange } },
    { text: " que carecen de coordenadas en el Anexo 2 oficial. Ver S8 para análisis detallado.", options: {} },
  ], {
    x: 0.38, y: 4.56, w: 9.1, h: 0.52,
    fontSize: 8.5, fontFace: "Calibri", color: C.textDark, margin: 0
  });
}

// ═══════════════════════════════════════
// S8 — SESGO DEL CENTROIDE (PANAMÁ)
// ═══════════════════════════════════════
{
  const s = pres.addSlide();
  addFrame(s, "Sesgo de Ubicación: El Caso Panamá (Piloto del Indicador)");

  s.addText("Panamá es el piloto porque tiene censo georreferenciado 2023. Este análisis ilustra el problema de los centroides en todos los países.", {
    x: 0.28, y: 0.76, w: 9.3, h: 0.3,
    fontSize: 9.5, fontFace: "Calibri", color: C.textMid, italic: true, margin: 0
  });

  // Left: school breakdown (compact height)
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.28, y: 1.15, w: 4.5, h: 2.15,
    fill: { color: C.offWhite }, line: { color: C.separator, pt: 1 }
  });
  s.addText("Composición de escuelas en Panamá", {
    x: 0.38, y: 1.22, w: 4.3, h: 0.28,
    fontSize: 10, fontFace: "Calibri", bold: true, color: C.navy, margin: 0
  });

  const panRows = [
    { label: "Total escuelas (piloto)",     n: "3,617", note: "", color: C.navy },
    { label: "  GPS de campo (Anexo 2)",     n: "3,070", note: "84.9%", color: C.green },
    { label: "  Centroide corregimiento",    n: "545",   note: "15.1%", color: C.orange },
    { label: "     Particulares sin GPS",    n: "519",   note: "99% centroides", color: C.orange },
    { label: "     Oficiales sin GPS",       n: "22",    note: "duplicadas", color: C.textLight },
    { label: "  Centroide distrito",         n: "2",     note: "excepcional", color: C.red },
    { label: "Particulares totales (MEDUCA)","n": "525", note: "sin GPS", color: C.textMid },
  ];
  panRows.forEach((r, i) => {
    const ry = 1.55 + i * 0.245;
    s.addText(r.label, {
      x: 0.42, y: ry, w: 2.9, h: 0.22,
      fontSize: 8.5, fontFace: "Calibri", color: r.color, margin: 0
    });
    s.addText(r.n, {
      x: 3.3, y: ry, w: 0.55, h: 0.22,
      fontSize: 8.5, fontFace: "Calibri", bold: true, color: r.color, align: "right", margin: 0
    });
    if (r.note) {
      s.addText(r.note, {
        x: 3.88, y: ry, w: 0.8, h: 0.22,
        fontSize: 7, fontFace: "Calibri", color: C.textLight, italic: true, margin: 0
      });
    }
  });

  // Right: impact analysis (compact)
  s.addShape(pres.shapes.RECTANGLE, {
    x: 5.0, y: 1.15, w: 4.6, h: 2.15,
    fill: { color: C.offWhite }, line: { color: C.separator, pt: 1 }
  });
  s.addText("Impacto en el indicador de accesibilidad", {
    x: 5.1, y: 1.22, w: 4.4, h: 0.28,
    fontSize: 10, fontFace: "Calibri", bold: true, color: C.navy, margin: 0
  });

  const impacts = [
    { icon: "+2-4 min", text: "Sesgo estimado: +2 a +4 min de viaje adicionales para hogares cerca de escuelas con centroide (vs. GPS real)." },
    { icon: "Rural",    text: "Distribucion geografica: los centroides se concentran en corregimientos rurales y periurbanos, donde el sesgo tiene mayor impacto." },
    { icon: "15.1%",    text: "En los 4 escenarios del piloto PAN, el 15.1% de escuelas con centroide introduce ruido. No invalida el analisis distrital, pero afecta el nivel corregimiento." },
    { icon: "Solucion", text: "Geocodificar 519 particulares (ver S9). Costo acotado vs. beneficio de eliminar el sesgo." },
  ];
  const impactColors = [C.orange, C.blue, C.navyMid, C.green];
  impacts.forEach((imp, i) => {
    const iy = 1.55 + i * 0.42;
    s.addShape(pres.shapes.RECTANGLE, {
      x: 5.1, y: iy + 0.02, w: 0.78, h: 0.2,
      fill: { color: impactColors[i] }, line: { color: impactColors[i] }
    });
    s.addText(imp.icon, {
      x: 5.1, y: iy + 0.02, w: 0.78, h: 0.2,
      fontSize: 7, fontFace: "Calibri", bold: true, color: C.white,
      align: "center", valign: "middle", margin: 0
    });
    s.addText(imp.text, {
      x: 5.92, y: iy, w: 3.55, h: 0.4,
      fontSize: 8.5, fontFace: "Calibri", color: C.textDark, margin: 0
    });
  });

  // Generalization note — moved up
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.28, y: 3.42, w: 9.3, h: 0.33,
    fill: { color: C.navy }, line: { color: C.navy }
  });
  s.addText("Extrapolacion a LAC: problema del centroide en otros paises", {
    x: 0.38, y: 3.42, w: 9.1, h: 0.33,
    fontSize: 9.5, fontFace: "Calibri", bold: true, color: C.white, valign: "middle", margin: 0
  });

  const lacRows = [
    ["Pais", "Sin coord", "% total", "Nivel de fallback actual"],
    ["Brasil (BRA)", "17,876", "13.3%", "Sin coordenadas en procesado — mayor brecha de LAC"],
    ["Argentina (ARG)", "1,469", "4.3%", "Sin coordenadas en procesado"],
    ["Costa Rica (CRI)", "37", "0.8%", "Sin coordenadas en procesado"],
    ["Colombia (COL)", "399", "0.9%", "Sin coordenadas en procesado"],
    ["Barbados (BRB)", "106", "100%", "CRITICO: procesado tiene cero coordenadas"],
  ];

  const lacRowH = 0.26;
  lacRows.forEach((row, i) => {
    const ry = 3.77 + i * lacRowH;
    const isHeader = i === 0;
    const bg = isHeader ? C.blueLight : (i % 2 === 0 ? C.white : C.offWhite);
    const tw = [1.55, 0.95, 0.75, 6.0];
    const tx = [0.28, 1.85, 2.82, 3.59];
    row.forEach((cell, j) => {
      s.addShape(pres.shapes.RECTANGLE, {
        x: tx[j], y: ry, w: tw[j], h: lacRowH,
        fill: { color: bg }, line: { color: C.separator, pt: 0.5 }
      });
      const isAlert = cell.includes("CRITICO") || (i > 0 && j === 2 && parseFloat(cell) > 5);
      s.addText(cell, {
        x: tx[j] + 0.04, y: ry + 0.04, w: tw[j] - 0.08, h: lacRowH - 0.06,
        fontSize: 8, fontFace: "Calibri",
        bold: isHeader || isAlert,
        color: isHeader ? C.navy : (isAlert ? C.red : C.textDark),
        margin: 0
      });
    });
  });
}

// ═══════════════════════════════════════
// S9 — DECISIÓN 2: ¿GEOCODIFICAR ANTES DEL 31?
// ═══════════════════════════════════════
{
  const s = pres.addSlide();
  addFrame(s, "Decisión 2: ¿Geocodificar Registros Faltantes Antes del 31 de Marzo?");

  // Decision banner (navy bg, gold accent left + right stripes)
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.28, y: 0.75, w: 9.3, h: 0.45,
    fill: { color: C.navy }, line: { color: C.navy }
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.28, y: 0.75, w: 0.25, h: 0.45,
    fill: { color: C.gold }, line: { color: C.gold }
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 9.33, y: 0.75, w: 0.25, h: 0.45,
    fill: { color: C.gold }, line: { color: C.gold }
  });
  s.addText("DECISIÓN REQUERIDA — AFECTA EL ALCANCE DEL PRIMER INDICADOR", {
    x: 0.55, y: 0.75, w: 8.75, h: 0.45,
    fontSize: 10, fontFace: "Calibri", bold: true,
    color: C.white, align: "center", valign: "middle", margin: 0
  });

  // Context
  s.addText("El 3.5% de escuelas sin coordenadas (20,833 registros) no pueden incluirse en el indicador. La mayor concentración está en Brasil (17,876), que representa el 14% de la base pública total de LAC.", {
    x: 0.28, y: 1.3, w: 9.3, h: 0.42,
    fontSize: 9.5, fontFace: "Calibri", color: C.textDark, margin: 0
  });

  // Two options
  const opts = [
    {
      label: "Opción A: Calcular con datos disponibles",
      color: C.blue,
      items: [
        "Publicar el indicador con 583k escuelas georeferenciadas (96.5% del total)",
        "Documentar el sesgo por país en los metadatos del indicador",
        "Brasil queda fuera del análisis completo de accesibilidad (13.3% sin coords)",
        "Panamá piloto completo al 100% (fallback de centroide ya implementado)",
        "Tiempo adicional: cero — listo para el 31 de marzo"
      ],
      pros: true
    },
    {
      label: "Opción B: Geocodificar antes del 31 de marzo",
      color: C.orange,
      items: [
        "Brasil: 17,876 escuelas — requiere API geocoding (Google/Nominatim) sobre dirección postal",
        "Panamá: 525 particulares — puede hacerse con búsqueda manual (Google Maps) dado el número pequeño",
        "Otros (ARG 1,469; COL 399; CRI 37): factibles con geocoding automático de direcciones",
        "Riesgo: calidad variable del geocoding automático; requiere validación manual de outliers",
        "Tiempo estimado: 3–5 días para Brasil; 1 día para PAN si se prioriza"
      ],
      pros: false
    },
  ];

  opts.forEach((opt, i) => {
    const ox = 0.28 + i * 4.78, oy = 1.82;
    s.addShape(pres.shapes.RECTANGLE, {
      x: ox, y: oy, w: 4.55, h: 2.95,
      fill: { color: C.offWhite }, line: { color: opt.color, pt: 1.5 }
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: ox, y: oy, w: 4.55, h: 0.38,
      fill: { color: opt.color }, line: { color: opt.color }
    });
    s.addText(opt.label, {
      x: ox + 0.1, y: oy, w: 4.35, h: 0.38,
      fontSize: 9.5, fontFace: "Calibri", bold: true,
      color: C.white, valign: "middle", margin: 0
    });
    opt.items.forEach((item, j) => {
      const iy = oy + 0.46 + j * 0.47;
      s.addShape(pres.shapes.OVAL, {
        x: ox + 0.12, y: iy + 0.08, w: 0.13, h: 0.13,
        fill: { color: opt.color }, line: { color: opt.color }
      });
      s.addText(item, {
        x: ox + 0.32, y: iy, w: 4.12, h: 0.42,
        fontSize: 8.5, fontFace: "Calibri", color: C.textDark, margin: 0
      });
    });
  });

  // Recommendation
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.28, y: 4.88, w: 9.3, h: 0.48,
    fill: { color: C.blueLight }, line: { color: C.blue, pt: 1 }
  });
  s.addText([
    { text: "Recomendación: ", options: { bold: true } },
    { text: "Opción B parcial — geocodificar solo Panamá (piloto) antes del 31 para eliminar el sesgo del centroide en el primer indicador publicado. Programar Brasil para Q2 2026 con pipeline automático de direcciones.", options: {} },
  ], {
    x: 0.38, y: 4.93, w: 9.1, h: 0.38,
    fontSize: 9, fontFace: "Calibri", color: C.navyMid, margin: 0
  });
}

// ═══════════════════════════════════════
// S10 — PAÍSES CON DATOS INCOMPLETOS
// ═══════════════════════════════════════
{
  const s = pres.addSlide();
  addFrame(s, "Países con Datos Incompletos: Casos Prioritarios");

  s.addText("Tres tipos de problemas identificados que requieren atención antes o después del primer indicador.", {
    x: 0.28, y: 0.76, w: 9.3, h: 0.3,
    fontSize: 9.5, fontFace: "Calibri", color: C.textMid, italic: true, margin: 0
  });

  const issues = [
    {
      priority: "CRÍTICO", color: C.red, bg: C.redLight,
      country: "Barbados (BRB)",
      issue: "El archivo procesado tiene 106 registros pero cero coordenadas (lat/lon). El archivo de entrada sí lista escuelas pero el script no extrajo coordenadas.",
      action: "Revisar script BRB — probable problema de nombres de columna. Solución inmediata (~1h)."
    },
    {
      priority: "CRÍTICO", color: C.red, bg: C.redLight,
      country: "Haití (HTI)",
      issue: "Cero cobertura en la plataforma. El archivo ministerial (.xls) requiere xlrd que no está instalado. OSM solo tiene 5,284 de ~15,000–18,000 escuelas reales. ~80-90% son privadas.",
      action: "Instalar xlrd y procesar el archivo MENFP 2022. Mayor impacto por bajo costo. Prioridad máxima para Fase 2."
    },
    {
      priority: "ALTA", color: C.orange, bg: C.orangeLight,
      country: "Perú (PER) — Bug de pipeline",
      issue: "La base procesada tiene 3,879 filas duplicadas exactas (mismo id_centro, mismas coordenadas). Bug confirmado: 2,416 escuelas con duplicados. Denominador incorrecto: 88,019 cod_mods vs. 68,957 locales únicos (ESCALE).",
      action: "Deduplicar por id_centro y actualizar denominador en school_coverage_assessment.py. Solución: ~2h."
    },
    {
      priority: "ALTA", color: C.orange, bg: C.orangeLight,
      country: "Jamaica (JAM)",
      issue: "Script R es un placeholder vacío. No hay archivo crudo de ministerio. La base procesada tiene 955 escuelas pero la fuente no está documentada. Universo real: ~1,050–1,200 incluyendo privadas.",
      action: "Conseguir archivo ministerial del MOE Jamaica. Baja prioridad para el 31 de marzo."
    },
    {
      priority: "MEDIA", color: C.blue, bg: C.blueLight,
      country: "Bahamas (BHS)",
      issue: "Solo 77 POIs de OSM — únicamente gobierno. Sin archivo ministerial disponible. Universo real desconocido.",
      action: "Contactar MOE Bahamas o usar directorio UNICEF. Fase 2."
    },
  ];

  issues.forEach((iss, i) => {
    const iy = 1.10 + i * 0.82;
    const rowH = 0.74;
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.28, y: iy, w: 9.3, h: rowH,
      fill: { color: iss.bg }, line: { color: iss.color, pt: 1 }
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.28, y: iy, w: 0.06, h: rowH,
      fill: { color: iss.color }, line: { color: iss.color }
    });
    // Badge
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.42, y: iy + 0.09, w: 0.98, h: 0.22,
      fill: { color: iss.color }, line: { color: iss.color }
    });
    s.addText(iss.priority, {
      x: 0.42, y: iy + 0.09, w: 0.98, h: 0.22,
      fontSize: 7, fontFace: "Calibri", bold: true,
      color: C.white, align: "center", valign: "middle", margin: 0
    });
    s.addText(iss.country, {
      x: 1.48, y: iy + 0.05, w: 3.0, h: 0.26,
      fontSize: 10, fontFace: "Calibri", bold: true, color: C.navy, margin: 0
    });
    s.addText(iss.issue, {
      x: 0.42, y: iy + 0.32, w: 5.1, h: 0.36,
      fontSize: 8, fontFace: "Calibri", color: C.textDark, margin: 0
    });
    // Action
    s.addShape(pres.shapes.RECTANGLE, {
      x: 5.65, y: iy + 0.07, w: 3.8, h: 0.6,
      fill: { color: C.white }, line: { color: C.separator, pt: 0.5 }
    });
    s.addText([
      { text: "Acción: ", options: { bold: true, color: C.navy } },
      { text: iss.action, options: { color: C.textDark } },
    ], {
      x: 5.72, y: iy + 0.10, w: 3.65, h: 0.52,
      fontSize: 8, fontFace: "Calibri", margin: 0
    });
  });
}

// ═══════════════════════════════════════
// S11 — PRÓXIMOS PASOS
// ═══════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.navy };

  // Left blue stripe
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 0.55, h: 5.625,
    fill: { color: C.blue }, line: { color: C.blue }
  });
  // Gold bottom bar
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 5.14, w: 10, h: 0.07,
    fill: { color: C.gold }, line: { color: C.gold }
  });

  s.addText("Próximos Pasos", {
    x: 0.75, y: 0.18, w: 8.8, h: 0.5,
    fontSize: 22, fontFace: "Calibri", bold: true, color: C.white, margin: 0
  });
  s.addText("Camino al primer indicador — entrega 31 de marzo de 2026", {
    x: 0.75, y: 0.65, w: 8.8, h: 0.3,
    fontSize: 11, fontFace: "Calibri", color: "A8C9E8", margin: 0
  });

  // Gold divider
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.75, y: 1.0, w: 8.8, h: 0.04,
    fill: { color: C.gold }, line: { color: C.gold }
  });

  const steps = [
    {
      num: "01",
      title: "Reunión BID",
      date: "Esta semana",
      items: [
        "Decisión 1: ¿incluir escuelas privadas?",
        "Decisión 2: ¿geocodificar Panamá antes del 31?",
        "Validar definición del indicador (15/30/60 min)",
      ],
      color: C.gold
    },
    {
      num: "02",
      title: "Correcciones técnicas",
      date: "22–26 Mar",
      items: [
        "Deduplicar PER (bug pipeline)",
        "Corregir BRB (cero coordenadas)",
        "Geocodificar PAN particulares (si aprobado)",
      ],
      color: C.blue
    },
    {
      num: "03",
      title: "Cálculo del indicador",
      date: "26–30 Mar",
      items: [
        "Ejecutar 4 escenarios Panamá (ya listos)",
        "Expandir a 19 países con datos completos",
        "Validar resultados distritales vs. literatura",
      ],
      color: C.blueMid
    },
    {
      num: "04",
      title: "Entrega Fase 1",
      date: "31 Mar 2026",
      items: [
        "Dashboard de resultados con 21 países",
        "Nota metodológica + metadatos por país",
        "Plan de Fase 2 (HTI, BHS, geocoding BRA)",
      ],
      color: "02C39A"
    },
  ];

  steps.forEach((st, i) => {
    const sx = 0.75 + i * 2.3, sy = 1.15;
    s.addShape(pres.shapes.RECTANGLE, {
      x: sx, y: sy, w: 2.05, h: 3.65,
      fill: { color: "0A2240" }, line: { color: st.color, pt: 1 }
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: sx, y: sy, w: 2.05, h: 0.06,
      fill: { color: st.color }, line: { color: st.color }
    });
    s.addText(st.num, {
      x: sx + 0.1, y: sy + 0.1, w: 0.6, h: 0.5,
      fontSize: 22, fontFace: "Calibri", bold: true, color: st.color, margin: 0
    });
    s.addText(st.title, {
      x: sx + 0.1, y: sy + 0.58, w: 1.85, h: 0.38,
      fontSize: 11, fontFace: "Calibri", bold: true, color: C.white, margin: 0
    });
    // Date badge
    s.addShape(pres.shapes.RECTANGLE, {
      x: sx + 0.1, y: sy + 0.96, w: 1.85, h: 0.24,
      fill: { color: st.color, transparency: 80 }, line: { color: st.color, pt: 0.5 }
    });
    s.addText(st.date, {
      x: sx + 0.1, y: sy + 0.96, w: 1.85, h: 0.24,
      fontSize: 8, fontFace: "Calibri", bold: true, color: st.color,
      align: "center", valign: "middle", margin: 0
    });
    // Items
    st.items.forEach((item, j) => {
      const iy = sy + 1.32 + j * 0.67;
      s.addShape(pres.shapes.RECTANGLE, {
        x: sx + 0.1, y: iy, w: 0.04, h: 0.42,
        fill: { color: st.color }, line: { color: st.color }
      });
      s.addText(item, {
        x: sx + 0.22, y: iy, w: 1.73, h: 0.42,
        fontSize: 8.5, fontFace: "Calibri", color: "A8C9E8", margin: 0
      });
    });
  });

  // Footer
  s.addText("BID — Plataforma de Indicadores Geoespaciales de Educación — LAC 2025/26  |  Entrega: 31 marzo 2026", {
    x: 0.75, y: 5.22, w: 8.8, h: 0.2,
    fontSize: 7.5, fontFace: "Calibri", color: "4A6B8A", margin: 0
  });
}

// ── Write file ──
const outPath = "/sessions/wizardly-adoring-rubin/mnt/accessibility_platform/results/BID_Accesibilidad_Escolar_LAC.pptx";
pres.writeFile({ fileName: outPath })
  .then(() => console.log("✓ PPT written to:", outPath))
  .catch(e => { console.error("✗ Error:", e.message); process.exit(1); });
