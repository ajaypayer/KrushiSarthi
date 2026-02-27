const search = document.getElementById("search");
const category = document.getElementById("category");
const crop = document.getElementById("crop");

const cards = document.querySelectorAll(".scheme-card");

function filterSchemes() {
  const searchText = search.value.toLowerCase();
  const cat = category.value;
  const cropValue = crop.value;

  cards.forEach(card => {
    const title = card.innerText.toLowerCase();
    const cardCat = card.dataset.category;
    const cardCrop = card.dataset.crop;

    const matchSearch = title.includes(searchText);
    const matchCategory = cat === "all" || cardCat === cat;
    const matchCrop = cropValue === "all" || cardCrop === cropValue;

    if (matchSearch && matchCategory && matchCrop) {
      card.style.display = "block";
    } else {
      card.style.display = "none";
    }
  });
}

search.addEventListener("keyup", filterSchemes);
category.addEventListener("change", filterSchemes);
crop.addEventListener("change", filterSchemes);