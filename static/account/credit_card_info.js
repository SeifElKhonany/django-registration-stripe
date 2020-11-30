
$(document).ready(function() {
    var stripe = Stripe('pk_test_Lhdb6MLLtbGrjsQxWBlEpO4U00cRpy5LDf');   // Stripe's publishable key

    var elements = stripe.elements();                                    // Stripe's elements
    var cardElement = elements.create('card');                           // Element to input card no., expiry, CVC and ZIP
    var cardButton = document.getElementById('card-button');
    var errorDisplay = $("#error-code");
    var successDisplay = $("#error-code");
    var cardButton = $('#card-button');                                  // Confirm new card button
    var defaultButton = $('#default-button');                            // Pay with default card button


    // Use Stripe's Card element to collect card info
    cardElement.mount('#card-element');

    // Pay with new card
    cardButton.click(function(ev) {

     ev.preventDefault();
     cardButton.attr('disabled', true);
     defaultButton.attr('disabled', true);

     // Create a payment method to attach to the customer
     stripe.createPaymentMethod({
         type: 'card',
         card: cardElement,
         billing_details: {
           name: $('#cardholder-name').val(),
         },
       }).then(function(result) {
         if (result.error) {
           errorDisplay.html(result.error.code);
           errorDisplay.show();
           cardButton.attr('disabled', false);
           defaultButton.attr('disabled', false);
         }
         else {
           // convert payment method to a string to be sent to the view
           var paymentMethod = JSON.stringify(result.paymentMethod);

           $.post("subscribe/",
           {
             // token required to avoid Cross-Site Request Forgery attacks
             'csrfmiddlewaretoken': csrf,
             'payment_method': paymentMethod,
             'user': user
           }).done(function(result) {
             if (result.error) {
               errorDisplay.html(result.error);
               errorDisplay.show();
               cardButton.attr('disabled', false);
               defaultButton.attr('disabled', false);
             }
             // Card requires user authentication
             else if (result.status == "requires_action") {
                stripe.confirmCardSetup(result.client_secret).then(function(result) {

                   if (result.error) {
                     errorDisplay.html('Card saved but its authentication is required to subscribe successfully');
                     errorDisplay.show();
                     cardButton.attr('disabled', false);
                     defaultButton.attr('disabled', false);
                     $.post("/profile/cancel_sub/",
                     {
                       'csrfmiddlewaretoken': csrf,
                       'user': user,
                     });
                   }
                   else {
                     // Navigate to profile
                     window.location.href = "/profile/";
                   }
                });
             }
             else {
                // Navigate to profile
                window.location.href = "/profile/";
             }
           });
         }
       });
    });

    // Use the user's default card to subscribe
    defaultButton.click(function(ev) {
      ev.preventDefault();
      cardButton.attr('disabled', true);
      defaultButton.attr('disabled', true);
      $.post("subscribe/",
        {
          'csrfmiddlewaretoken': csrf,
          'user': user
        }).done(function(result) {
          if (result.error) {
            errorDisplay.html(result.error);
            errorDisplay.show();
            cardButton.attr('disabled', false);
            defaultButton.attr('disabled', false);
          }
          // Card requires user authentication
          else if (result.status == "requires_action") {
            stripe.confirmCardSetup(result.client_secret).then(function(result) {
              if (result.error) {
                errorDisplay.html('requires authentication');
                errorDisplay.show();
                cardButton.attr('disabled', false);
                defaultButton.attr('disabled', false);
              }
              else {
                // Navigate to profile
                window.location.href = "/profile/";
              }
            });
          }
          else {
            window.location.href = "/profile/";
          }
        });
    });

});
