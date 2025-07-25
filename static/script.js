let currentIndex = 0;
const slides = document.querySelectorAll('.carousel-slide img');
const totalSlides = slides.length;
const slideInterval = 2500;  // 3 seconds for each slide

// Move to the next slide
function moveToNextSlide() {
  currentIndex = (currentIndex + 1) % totalSlides;  // Loop back to the first slide
  const newTransformValue = -currentIndex * 100; // Moves the slides by 100% for each image
  document.querySelector('.carousel-slide').style.transform = `translateX(${newTransformValue}%)`;

  // Set the next slide after the interval
  setTimeout(moveToNextSlide, slideInterval);
}

// Start the carousel after the first interval
setTimeout(moveToNextSlide, slideInterval);