// ---------------> SCROLL - BAR <---------------
{
  const body = document.body;
  let lastScroll = 0;

  window.addEventListener("scroll", () => {
    const currentScroll = window.pageYOffset;

    if (currentScroll <= 0) {
      body.classList.remove("scroll-up");
    }

    if (currentScroll > lastScroll && !body.classList.contains("scroll-down")) {
      body.classList.remove("scroll-up");
      body.classList.add("scroll-down");
    }

    if (currentScroll < lastScroll && body.classList.contains("scroll-down")) {
      body.classList.remove("scroll-down");
      body.classList.add("scroll-up");
    }

    lastScroll = currentScroll;
  });
}

// ---------------> TOGGLE - NAV <---------------
{
  const btnToggle = document.querySelector(".btn-toggle_nav");
  const navMenu = document.querySelector(".nav-menu");

  btnToggle.addEventListener("click", () => {
    btnToggle.classList.toggle("active")
    navMenu.classList.toggle("active")
  })

  document.querySelectorAll(".nav-link").forEach(n => {
    n.addEventListener("click", () => {
      btnToggle.classList.remove("active")
      navMenu.classList.remove("active")
    })
  })
}


// ---------------> Drag & Drop <---------------
{
  const dropzone = document.getElementById("dropzone");
  const thumbnailInput = document.getElementById("thumbnail");
  const preview = document.getElementById("preview");
  
  dropzone.addEventListener("click", () => {
      thumbnailInput.click();
  });
  
  dropzone.addEventListener("dragover", (e) => {
      e.preventDefault();
      dropzone.classList.add("border-primary");
  });
  
  dropzone.addEventListener("dragleave", () => {
      dropzone.classList.remove("border-primary");
  });
  
  dropzone.addEventListener("drop", (e) => {
      e.preventDefault();
      dropzone.classList.remove("border-primary");
      const file = e.dataTransfer.files[0];
      handleFile(file);
  });
  
  thumbnailInput.addEventListener("change", (e) => {
      const file = e.target.files[0];
      handleFile(file);
  });
  
  function handleFile(file) {
      if (file && file.size <= 5 * 1024 * 1024) { // Max 5MB
          const reader = new FileReader();
          reader.onload = (e) => {
              preview.src = e.target.result;
              preview.classList.remove("d-none");
          };
          reader.readAsDataURL(file);
      } else {
          alert("File size must be less than 5MB.");
      }
  }
}

{
  document.getElementById('title').addEventListener('input', function () {
    let words = this.value.split(' ');
    this.value = words.map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()).join(' ');
});
}