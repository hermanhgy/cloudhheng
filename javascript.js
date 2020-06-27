window.onload = function cert_triangle()
{
    document.querySelectorAll('.accordion_butt').forEach(button => 
        {
            button.addEventListener('click', () => {
            button.classList.toggle('accordion_butt--active');
        });
    });

    document.querySelectorAll('.accordion_butt2').forEach(button => 
        {
            button.addEventListener('click', () => {
            button.classList.toggle('accordion_butt2--active');
        });
    });
}


function showSlides() {
    var i;
    var slides = document.getElementsByClassName("mySlides");
    var dots = document.getElementsByClassName("dot");
    for (i = 0; i < slides.length; i++) {
    slides[i].style.display = "none";  
    }
    slideIndex++;
    if (slideIndex > slides.length) {slideIndex = 1}    
    for (i = 0; i < dots.length; i++) {
    dots[i].className = dots[i].className.replace(" active", "");
    }
    slides[slideIndex-1].style.display = "block";  
    dots[slideIndex-1].className += " active";
    setTimeout(showSlides, 3000); // Change image every 3 seconds
}


function toggle_white() 
{
    var element =  document.querySelector(".small-button");
    element.classList.toggle("toggle-mode");
}


function display_alert()
{
    alert('This page is under construction. It will be coming soon!');
}


// When the user scrolls down 20px from the top of the document, show the button
window.onscroll = function() {scrollFunction()};

function scrollFunction() {
    var mybutton = document.getElementById("myBtn");
    if (document.body.scrollTop > 20 || document.documentElement.scrollTop > 20) {
    mybutton.style.display = "block";
    } else {
    mybutton.style.display = "none";
    }
}


// When the user clicks on the button, scroll to the top of the document
function topFunction() {
    document.body.scrollTop = 0;
    document.documentElement.scrollTop = 0;
}


// The script above for "Go Up" currently only works for small screen when two columns stack together
// To make the script works for large screen (for some long selected pages), the script needs to track the scroll element of the RIGHT pane
// Give the RIGHT pane a new ID called right2 as this -  <id="right2" onscroll="myFunction()">
// Then execute below javascript 
// ************************************************************************************************************
// function myFunction() {
//     var mybutton = document.getElementById("myBtn");
//     var elmnt = document.getElementById("right2");
//     if (document.getElementById("right2").scrollTop > 20) {
//     mybutton.style.display = "block";
//     } else {
//     mybutton.style.display = "none";
//     }
// }

// also need to create button new id and the copy the css -  <button onclick="topFunction2()" id="myBtn2" title="Go to top">&#8679;</button>
// function topFunction2() {
//     document.getElementById("right2").scrollTop = 0;
// }
// ************************************************************************************************************