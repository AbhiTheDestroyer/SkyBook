import test from'node:test';import assert from'node:assert/strict';import{DiscountEngine}from'../services/offers.js';
test('percentage discount is centralized',()=>{const x=DiscountEngine.calculate({fare:6000,offer:{discount_type:'PERCENTAGE',discount_value:15,maximum_discount:1500,promo_code:'SAVE15'},taxes:500,serviceFee:0,seatFee:300,addOns:0});assert.equal(x.discount,900);assert.equal(x.finalTotal,5900)});
test('maximum discount cap is enforced',()=>assert.equal(DiscountEngine.discount({discount_type:'PERCENTAGE',discount_value:20,maximum_discount:1500},10000),1500));
test('fixed amount cannot make fare negative',()=>assert.equal(DiscountEngine.discount({discount_type:'FIXED_AMOUNT',discount_value:1000,maximum_discount:null},400),400));
test('no offer leaves fare unchanged',()=>{const x=DiscountEngine.calculate({fare:5000,taxes:756,serviceFee:200});assert.equal(x.discount,0);assert.equal(x.finalTotal,5956)});
