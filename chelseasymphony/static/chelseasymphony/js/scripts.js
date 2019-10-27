$(document).ready(function() {
    //Creates accordion for mobile nav
    $('.nav-toggle button').on("click", function () {
        $('nav').toggleClass('active');
    });

    $('.past-seasons').on('click', function(event) {
        $('.past-seasons').toggleClass('active');
    });

    //Creates accordion toggle for email signup form
    $( ".email-subscribe" ).accordion({
        active: false,
        collapsible: true
    });

    $(document).on("click",function(e) {
        if (!$( ".email-subscribe" ).is(e.target) &&
            !$( ".email-subscribe" ).has(e.target).length) {
                $(".email-subscribe").accordion("option", "active", false);
            }
    });

    // Profile page
    function profilePage () {
        if ($(window).width() > 850) {
            $(".profile-info-container").append($(".profile-bio"));
            $(".profile-headshot-container").append($(".profile-info > .contact"));
        };
    }
    $(document).ready(profilePage);
    $(window).resize(profilePage);

    // Uncomment for homepage popup
    //let hpUrl = "https://" + document.domain + "/";
    //let referrer = document.referrer;
    //if (hpUrl == document.URL && !referrer.startsWith($hpUrl)) {
        //let popStyles = document.createElement('popup-style');
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

    // Donation Page
    // Toggle the single and recurring forms
    $("#donation-type-recurring").on("click", function () {
        $("#single-donation").hide();
        $("#recurring-donation").show();
    });

    $("#donation-type-single").on("click", function () {
        $("#single-donation").show();
        $("#recurring-donation").hide();
    });

    // Handle cases when someone hits back from PayPal and the recurring
    // donation field is selected - this ensures the recurring form values
    // are visible to the user.
    if ($("#donation-type-recurring").length &&
            $("#donation-type-recurring")[0].checked) {
        $("#single-donation").hide();
        $("#recurring-donation").show();
    }

    // Clear an invalid 'other' amount if another field is clicked
    $('.proxy-input').each(function(idx, el){
        var single = $('#single-other-amount')[0];
        var recurring = $('#recurring-other-amount')[0];

        if ((el.id !== 'single-other') && (el.id !== 'recurring-other')) {
            $(el).on('click', function(e){
                if (!single.checkValidity()) {
                    single.value = "";
                }
                if (!recurring.checkValidity()) {
                    recurring.value = "";
                }
            });
        }
    });

    // Set the 'other' amounts
    $('input[name=single_other_amount]').on('focus', function (e) {
        $('#single-other').prop('checked', true);
    });

    $('input[name=single_other_amount]').on('blur', function (e) {
        $('#single-other').attr('value', e.target.value);
    });

    $('input[name=recurring_other_amount]').on('focus', function (e) {
        $('#recurring-other').prop('checked', true);
    });

    $('input[name=recurring_other_amount]').on('blur', function (e) {
        $('#recurring-other').attr('value', e.target.value);
    });

    $("#proxy-form").on("submit", function (e) {
        e.preventDefault();
        let donationType = $('input[type=radio][name=donation_type]:checked').val();
        if (donationType === 'single') {
            let val = $('input[type=radio][name=single_donation]:checked').val();
            let donationAmount = val ? val : '0.00';
            $('#single-donation-form form input[name=amount]').attr('value', donationAmount);
            $('#single-donation-form form').submit();
        } else if (donationType === 'recurring') {
            let val = $('input[type=radio][name=recurring_donation]:checked').val();
            let donationAmount = val ? val : '0.00';
            $('#recurring-donation-form form input[name=a3]').attr('value', donationAmount);
            $('#recurring-donation-form form').submit();
        }
    });
});
