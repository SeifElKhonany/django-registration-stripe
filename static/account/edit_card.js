
function remove(element) {
    card_no = element.parentElement.getAttribute("data-no");
    card_id = element.parentElement.getAttribute("data-id");
    element.setAttribute('disabled', true);
    element.previousElementSibling.setAttribute('disabled', true);

    $.post("remove/",
     {
       'csrfmiddlewaretoken': csrf,
       'card_id': card_id,
       'card_no': card_no,
       'user': user
     })
      .done(function(data) {
         window.location.href = "/profile/";
    });
}

function makeDefault(element) {
    card_id = element.parentElement.getAttribute("data-id");
    element.setAttribute('disabled', true);
    element.nextElementSibling.setAttribute('disabled', true);

    $.post("make_default/",
     {
       'csrfmiddlewaretoken': csrf,
       'card_id': card_id,
       'user': user
     }).done(function() {
         window.location.href = "/profile/";
     });
}

$(document).ready(function() {

  var stripe = Stripe('pk_test_Lhdb6MLLtbGrjsQxWBlEpO4U00cRpy5LDf');

  var elements = stripe.elements();
  var cardElement = elements.create('card');
  var cardButton = document.getElementById('card-button');
  var errorDisplay = $("#error-code");
  var successDisplay = $("#error-code");
  var cardButton = $('#card-button');
  var defaultButton = $('#default-button');


  // Use Stripe's Card element to collect card info
  cardElement.mount('#card-element');


  /* For some reason loading the static path dynamically couldn't load the card logo even though it was correct, so
  this was the alternative */
  $(".card-brand").each(function(){
    var brand = this.getAttribute("src").split(static);
    var element = this;
    this.setAttribute("src", static + element.getAttribute("data-brand") + ".png");
  });

  // Card requires user authentication
  if (status == "requires_action") {
    stripe.confirmCardSetup(clientSecret).then(function(result) {
      if (result.error) {
        errorDisplay.html('requires authentication');
        errorDisplay.show();
      }
    });
  }

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
      } else {
        var paymentMethod = JSON.stringify(result.paymentMethod);

        $.post("add_card/",
        {
          'csrfmiddlewaretoken': csrf,
          'payment_method': paymentMethod,
          'user': user
        }).done(function(error) {
          if (error.error) {
            errorDisplay.html(error.error);
            errorDisplay.show();
          }
          else {
            window.location.href = "/profile/";
          }
        });
      }
    });
  });
});
