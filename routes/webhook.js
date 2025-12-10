const express = require('express');
const { MercadoPagoConfig, Payment } = require('mercadopago');
const { PrismaClient } = require('@prisma/client');
const { successResponse, errorResponse } = require('../utils/responses');

const router = express.Router();
const prisma = new PrismaClient();

const client = new MercadoPagoConfig({
  accessToken: process.env.MERCADOPAGO_ACCESS_TOKEN
});
const payment = new Payment(client);

// Webhook Mercado Pago
router.post('/mercadopago', async (req, res) => {
  try {
    const { type, data } = req.body;

    if (type === 'payment') {
      const paymentId = data.id;

      // Buscar informações do pagamento
      const paymentInfo = await payment.get({ id: paymentId });
      const orderIdStr = paymentInfo.external_reference;

      if (orderIdStr) {
        const orderId = parseInt(orderIdStr);
        const order = await prisma.order.findUnique({
          where: { id: orderId }
        });

        if (order) {
          const paymentStatus = paymentInfo.status;
          let newStatus = order.status;

          if (paymentStatus === 'approved') {
            newStatus = 'paid';

            // Reduzir estoque dos produtos
            for (const item of order.items) {
              await prisma.product.update({
                where: { id: item.product_id },
                data: {
                  estoque: {
                    decrement: item.quantidade
                  }
                }
              });
            }
          } else if (paymentStatus === 'cancelled' || paymentStatus === 'rejected') {
            newStatus = 'cancelled';
          }

          await prisma.order.update({
            where: { id: orderId },
            data: { status: newStatus }
          });
        }
      }
    }

    return successResponse(res, null, 'Webhook processado');

  } catch (error) {
    console.error(error);
    return errorResponse(res, 'Erro no webhook', 500);
  }
});

module.exports = router;