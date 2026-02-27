const cropFilter = document.getElementById("cropFilter");
const seasonFilter = document.getElementById("seasonFilter");
const rows = document.querySelectorAll("#mspTable tbody tr");

function filterMSP() {
  const crop = cropFilter.value;
  const season = seasonFilter.value;

  rows.forEach(row => {
    const rowCrop = row.dataset.crop;
    const rowSeason = row.dataset.season;

    const matchCrop = crop === "all" || crop === rowCrop;
    const matchSeason = season === "all" || season === rowSeason;

    if (matchCrop && matchSeason) {
      row.style.display = "";
    } else {
      row.style.display = "none";
    }
  });
}

cropFilter.addEventListener("change", filterMSP);
seasonFilter.addEventListener("change", filterMSP);