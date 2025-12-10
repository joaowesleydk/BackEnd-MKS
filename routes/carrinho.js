const express = require('express');
const { PrismaClient } = require('@prisma/client');
const { successResponse, errorResponse } = require('../utils/responses');
const { authenticateToken } = require('../middleware/auth');

const router = express.Router();
const prisma = new PrismaClient();

// Get carrinho
router.get('/', authenticateToken, async (req, res) => {
  try {
    const cartItems = await prisma.cartItem.findMany({
      where: { user_id: req.user.id },
      include: {
        product: true
      }
    });

    let total = 0;
    const items = cartItems.map(item => {
      if (item.product && item.product.is_active) {
        const precoAtual = item.product.promocao ? item.product.preco_promocional : item.product.preco;
        const subtotal = precoAtual * item.quantidade;
        total += subtotal;

        return {
          id: item.id,
          produto: {
            id: item.product.id,
            nome: item.product.nome,
            preco: item.product.preco,
            preco_promocional: item.product.preco_promocional,
            promocao: item.product.promocao,
            imagens: item.product.imagens,
            estoque: item.product.estoque
          },
          quantidade: item.quantidade,
          subtotal
        };
      }
      return null;
    }).filter(Boolean);

    return successResponse(res, { items, total }, 'Carrinho carregado');

  } catch (error) {
    console.error(error);
    return errorResponse(res, 'Erro interno do servidor', 500);
  }
});

// Adicionar ao carrinho
router.post('/adicionar', authenticateToken, async (req, res) => {
  try {
    const { produto_id, quantidade = 1 } = req.body;

    const product = await prisma.product.findFirst({
      where: {
        id: produto_id,
        is_active: true
      }
    });

    if (!product) {
      return errorResponse(res, 'Produto não encontrado', 404);
    }

    if (product.estoque < quantidade) {
      return errorResponse(res, 'Estoque insuficiente', 400);
    }

    const existingItem = await prisma.cartItem.findFirst({
      where: {
        user_id: req.user.id,
        product_id: produto_id
      }
    });

    if (existingItem) {
      await prisma.cartItem.update({
        where: { id: existingItem.id },
        data: { quantidade: existingItem.quantidade + quantidade }
      });
    } else {
      await prisma.cartItem.create({
        data: {
          user_id: req.user.id,
          product_id: produto_id,
          quantidade
        }
      });
    }

    return successResponse(res, null, 'Item adicionado ao carrinho');

  } catch (error) {
    console.error(error);
    return errorResponse(res, 'Erro interno do servidor', 500);
  }
});

// Update item carrinho
router.put('/item/:id', authenticateToken, async (req, res) => {
  try {
    const { id } = req.params;
    const { quantidade } = req.body;

    const cartItem = await prisma.cartItem.findFirst({
      where: {
        id: parseInt(id),
        user_id: req.user.id
      }
    });

    if (!cartItem) {
      return errorResponse(res, 'Item não encontrado', 404);
    }

    if (quantidade <= 0) {
      await prisma.cartItem.delete({
        where: { id: parseInt(id) }
      });
    } else {
      await prisma.cartItem.update({
        where: { id: parseInt(id) },
        data: { quantidade }
      });
    }

    return successResponse(res, null, 'Carrinho atualizado');

  } catch (error) {
    console.error(error);
    return errorResponse(res, 'Erro interno do servidor', 500);
  }
});

// Remove item carrinho
router.delete('/item/:id', authenticateToken, async (req, res) => {
  try {
    const { id } = req.params;

    const cartItem = await prisma.cartItem.findFirst({
      where: {
        id: parseInt(id),
        user_id: req.user.id
      }
    });

    if (!cartItem) {
      return errorResponse(res, 'Item não encontrado', 404);
    }

    await prisma.cartItem.delete({
      where: { id: parseInt(id) }
    });

    return successResponse(res, null, 'Item removido do carrinho');

  } catch (error) {
    console.error(error);
    return errorResponse(res, 'Erro interno do servidor', 500);
  }
});

// Limpar carrinho
router.delete('/limpar', authenticateToken, async (req, res) => {
  try {
    await prisma.cartItem.deleteMany({
      where: { user_id: req.user.id }
    });

    return successResponse(res, null, 'Carrinho limpo');

  } catch (error) {
    console.error(error);
    return errorResponse(res, 'Erro interno do servidor', 500);
  }
});

module.exports = router;