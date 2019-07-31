// var prevScrollpos = window.pageYOffset;
// window.onscroll = function() {
//   var currentScrollPos = window.pageYOffset;
//   if (prevScrollpos > currentScrollPos) {
//     $("#footer_toggle").slideDown();
//   } 
//   else {
//     $("#footer_toggle").slideUp();
//   }
//   prevScrollpos = currentScrollPos;

// } 

var isToggled = false;
function toggleLanguage(){
  $('#footer_toggle').animate({'bottom': (isToggled ? '30px' : '70px')});
  isToggled = !isToggled;
  $('#language_footer').slideToggle();
}
