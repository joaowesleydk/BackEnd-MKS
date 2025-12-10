const express = require('express');
const axios = require('axios');
const { PrismaClient } = require('@prisma/client');
const { successResponse, errorResponse } = require('../utils/responses');
const { authenticateToken } = require('../middleware/auth');

const router = express.Router();
const prisma = new PrismaClient();

const calculateShipping = (cep, total) => {
  // Frete grátis acima de R$ 150
  if (total >= 150.0) {
    return { frete: 0.0, prazo: 5 };
  }

  // Frete por estado (simulação)
  const fretePorEstado = {
    'SP': 10.0, 'RJ': 12.0, 'MG': 15.0, 'RS': 18.0,
    'PR': 16.0, 'SC': 17.0, 'GO': 20.0, 'DF': 18.0,
    'BA': 22.0, 'PE': 25.0, 'CE': 28.0, 'AM': 35.0
  };

  // Simular busca do estado pelo CEP (simplificado)
  const uf = 'SP'; // Seria obtido via ViaCEP
  const frete = fretePorEstado[uf] || 20.0;
  const prazo = ['SP', 'RJ', 'MG'].includes(uf) ? 7 : 10;

  return { frete, prazo };
};

// Calcular frete
router.post('/calcular', authenticateToken, async (req, res) => {
  try {
    const { cep } = req.body;

    // Calcular total do carrinho
    const cartItems = await prisma.cartItem.findMany({
      where: { user_id: req.user.id },
      include: { product: true }
    });

    if (cartItems.length === 0) {
      return errorResponse(res, 'Carrinho vazio', 400);
    }

    let total = 0;
    for (const item of cartItems) {
      if (item.product) {
        const precoAtual = item.product.promocao ? item.product.preco_promocional : item.product.preco;
        total += precoAtual * item.quantidade;
      }
    }

    const shippingInfo = calculateShipping(cep, total);

    return successResponse(res, shippingInfo, 'Frete calculado com sucesso');

  } catch (error) {
    console.error(error);
    return errorResponse(res, 'Erro interno do servidor', 500);
  }
});

module.exports = router;