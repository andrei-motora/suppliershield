/** Export an array of objects as a CSV file download. */

function escapeCsvField(value: unknown): string {
  const str = value == null ? "" : String(value);
  return str.includes(",") || str.includes('"') || str.includes("\n")
    ? `"${str.replace(/"/g, '""')}"`
    : str;
}

export function exportCsv(data: Record<string, unknown>[], filename: string) {
  if (data.length === 0) return;
  const headers = Object.keys(data[0]);
  const headerRow = headers.map(escapeCsvField).join(",");
  const rows = data.map((row) =>
    headers.map((h) => escapeCsvField(row[h])).join(",")
  );
  const csv = [headerRow, ...rows].join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
