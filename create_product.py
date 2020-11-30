 import stripe

 stripe.api_key = '{ Your sk }'

 product = stripe.Product.create(
   name='WhatsBusy Membership',
 )

 price = stripe.Price.create(
   product=product.id,
   unit_amount=4999,
   currency='usd',
   recurring={
     'interval': 'month',
   },
 )

 print(price.id)