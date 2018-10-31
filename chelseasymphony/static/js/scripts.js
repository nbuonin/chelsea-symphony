// $(document).ready(function() {
//   //Creates accordion toggle for email signup form
//   $('.nav-toggle button').on("click", function () {
//     $('nav').toggleClass('active');
//   });

//   $(function() {
//     $( ".email-subscribe" ).accordion({
//         active: false,
//         collapsible: true
//     });
//   });

//   $(document).on("click",function(e) {
//     if (!$( ".email-subscribe" ).is(e.target) && !$( ".email-subscribe" ).has(e.target).length) {
//         $(".email-subscribe").accordion("option", "active", false);
//     }
//   });

//   // modifies markup of profile page for RWD
//   function profilePage () {
//     if ($(window).width() > 850) {
//       $(".profile-info-container").append($(".profile-bio"));
//       $(".profile-headshot-container").append($(".profile-info > .contact"));
//     };
//   }

//   $(document).ready(profilePage);
//   $(window).resize(profilePage);
// });


// All the stuff above needs to be Drupalized ^^^^^^^^^^^^

(function ($) {
  Drupal.behaviors.navToggle = {
    attach: function(context, settings) { // start writing JS from here
      //Creates accordion for mobile nav
      $('.nav-toggle button').on("click", function () {
        $('nav').toggleClass('active');
      });
    }
  }

  Drupal.behaviors.signupToggle = {
    attach: function(context, settings) { // start writing JS from here
      //Creates accordion toggle for email signup form
      $( ".email-subscribe" ).accordion({
          active: false,
          collapsible: true
      });

      $(document).on("click",function(e) {
        if (!$( ".email-subscribe" ).is(e.target) && !$( ".email-subscribe" ).has(e.target).length) {
            $(".email-subscribe").accordion("option", "active", false);
        }
      });
    }
  }

  Drupal.behaviors.profilePageSwap = {
    attach: function(context, settings) { // start writing JS from here
      function profilePage () {
        if ($(window).width() > 850) {
          $(".profile-info-container").append($(".profile-bio"));
          $(".profile-headshot-container").append($(".profile-info > .contact"));
        };
      }

      $(document).ready(profilePage);
      $(window).resize(profilePage);
    }
  }

  // This toggled the single payment form
  // Drupal.behaviors.donatePageToggle = {
  //   attach: function(context, settings) { // start writing JS from here
  //     //Creates accordion for mobile nav
  //     $('#block-paypal-donations-paypal-donations-single h3').on("click", function () {
  //       $('#block-paypal-donations-paypal-donations-single form').toggleClass('active');
  //     });
  //   }
  // }

  //Uncomment this to activate homepage modal
  //Drupal.behaviors.homePageModal = {
    //attach: function(context, settings) { // start writing JS from here
      //$hpUrl = "https://" + document.domain + "/";
      //$referrer = document.referrer;
      ////if ($hpUrl == document.URL && !$referrer.startsWith($hpUrl)) {
      //if ($hpUrl == document.URL) {
        //var popStyles = document.createElement('popup-style');
        //popStyles.type = 'text/css';
        //popStyles.innerHTML= '.mfp-iframe-holder .mfp-content { line-height: 0; width: 100%; max-width: 400px; }'
        //document.getElementsByTagName('head')[0].appendChild(popStyles);
        //jQuery.magnificPopup.open({
          //items: {
              //src: $('<div style="background-color: white; margin: 0 auto;  max-width: 450px; padding: 2em; text-align: center;">' +
                           //'Looking for The Chelsea Symphony\'s paperless program?<br/><br/>' +
                           //'<a href="https://chelseasymphony.org/earth-day-2018"><button style="margin: 0 auto;">Click Here</button></a><br/>' +
                           //'American Museum of Natural History<br/>' +
                           //'Milstein Hall of Ocean Life<br/>' +
                           //'EarthFest<br/><br/>' +
                         //'Sunday, April 22 at 2pm<br/>')
          //},
          //showCloseBtn: false,
          //type:'inline'
        //}, 0);
      //}
    //}
  //}

  // Drupal.behaviors.googleAnalyticsSingleDonationEvent = {
  //   attach: function(context, settings) { // start writing JS from here
  //     $("form.single-donation-form .donation-submit-button").click(function(){
  //       $val = $("form.single-donation-form input.amount-holder").attr("value");

  //       ga('send', {
  //         hitType: 'event',
  //         eventCategory: 'Donation',
  //         eventAction: 'Single_Donation',
  //         eventValue: $val,
  //       });
  //     });
  //   }
  // }

  // Drupal.behaviors.googleAnalyticsRecurringDonationEvent = {
  //   attach: function(context, settings) { // start writing JS from here
  //     $("form.monthly-donation-form .donation-submit-button").click(function(){
  //       $val = $("form.monthly-donation-form input.amount-holder").attr("value");

  //       ga('send', {
  //         hitType: 'event',
  //         eventCategory: 'Donation',
  //         eventAction: 'Monthy_Donation',
  //         eventValue: $val,
  //       });
  //     });
  //   }
  // }
})
(jQuery);

