const express = require('express');
const mercadopago = require('mercadopago');
const { PrismaClient } = require('@prisma/client');
const { successResponse, errorResponse } = require('../utils/responses');
const { authenticateToken } = require('../middleware/auth');

const router = express.Router();
const prisma = new PrismaClient();

mercadopago.configure({
  access_token: process.env.MERCADOPAGO_ACCESS_TOKEN
});

// Criar pagamento Mercado Pago
router.post('/mercadopago', authenticateToken, async (req, res) => {
  try {
    const { endereco, frete, payment_method = 'pix' } = req.body;

    // Verificar carrinho
    const cartItems = await prisma.cartItem.findMany({
      where: { user_id: req.user.id },
      include: { product: true }
    });

    if (cartItems.length === 0) {
      return errorResponse(res, 'Carrinho vazio', 400);
    }

    // Calcular total e preparar items
    let total = 0;
    const items = [];

    for (const cartItem of cartItems) {
      const product = cartItem.product;
      
      if (!product || !product.is_active) {
        return errorResponse(res, `Produto ${cartItem.product_id} não disponível`, 400);
      }

      if (product.estoque < cartItem.quantidade) {
        return errorResponse(res, `Estoque insuficiente para ${product.nome}`, 400);
      }

      const precoAtual = product.promocao ? product.preco_promocional : product.preco;
      const subtotal = precoAtual * cartItem.quantidade;
      total += subtotal;

      items.push({
        product_id: product.id,
        nome: product.nome,
        preco: precoAtual,
        quantidade: cartItem.quantidade,
        subtotal
      });
    }

    const totalComFrete = total + frete;

    // Criar pedido
    const order = await prisma.order.create({
      data: {
        user_id: req.user.id,
        total: totalComFrete,
        frete,
        endereco,
        items,
        payment_method
      }
    });

    // Criar pagamento no Mercado Pago
    const payment = {
      transaction_amount: totalComFrete,
      description: `Pedido Moda Karina Store #${order.id}`,
      payment_method_id: payment_method,
      payer: {
        email: req.user.email,
        first_name: req.user.nome
      },
      external_reference: order.id.toString(),
      notification_url: `https://backend-mks-1.onrender.com/webhook/mercadopago`
    };

    const paymentResponse = await mercadopago.payment.create(payment);

    // Atualizar pedido com payment_id
    await prisma.order.update({
      where: { id: order.id },
      data: { payment_id: paymentResponse.body.id.toString() }
    });

    // Limpar carrinho
    await prisma.cartItem.deleteMany({
      where: { user_id: req.user.id }
    });

    return successResponse(res, {
      order_id: order.id,
      payment: paymentResponse.body
    }, 'Pagamento criado com sucesso');

  } catch (error) {
    console.error(error);
    return errorResponse(res, 'Erro ao criar pagamento', 500);
  }
});

module.exports = router;