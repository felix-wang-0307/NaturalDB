import axios from 'axios';
import type {
  QueryRequest,
  QueryResponse,
  AggregationRequest,
  AggregationResponse,
  CountResponse,
  Product,
  Review,
} from '../types';

// API 基础配置
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';
const USER_ID = 'demo_user';
const DB_NAME = 'amazon';

// 创建 axios 实例
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 响应拦截器
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// ============ 健康检查 ============
export const healthCheck = () => api.get('/health');

// ============ 查询 API ============

/**
 * 执行通用查询
 */
export const query = <T = Product>(params: QueryRequest): Promise<QueryResponse<T>> => {
  return api.post(`/api/databases/${USER_ID}/${DB_NAME}/query`, params);
};

/**
 * 获取所有商品（支持分页和过滤）
 */
export const getProducts = (params: {
  limit?: number;
  skip?: number;
  filters?: QueryRequest['filters'];
  sort?: QueryRequest['sort'];
}): Promise<QueryResponse<Product>> => {
  return query<Product>({
    table: 'Products',
    ...params,
  });
};

/**
 * 根据 ID 获取单个商品
 */
export const getProductById = (productId: string) => {
  return api.get(
    `/api/databases/${USER_ID}/${DB_NAME}/tables/Products/records/${productId}`
  );
};

/**
 * 获取商品评论
 */
export const getProductReviews = (productId: string): Promise<QueryResponse<Review>> => {
  return query<Review>({
    table: 'Reviews',
    filters: [{ field: 'product_id', operator: 'eq', value: productId }],
  });
};

/**
 * 搜索商品（按名称）
 */
export const searchProducts = (searchText: string, limit = 50): Promise<QueryResponse<Product>> => {
  return query<Product>({
    table: 'Products',
    filters: [
      { field: 'product_name', operator: 'contains', value: searchText },
    ],
    limit,
  });
};

/**
 * 获取类别列表
 */
export const getCategories = () => {
  return api.get(`/api/databases/${USER_ID}/${DB_NAME}/tables/Categories/records`);
};

/**
 * 按类别筛选商品
 */
export const getProductsByCategory = (
  category: string,
  limit = 50
): Promise<QueryResponse<Product>> => {
  return query<Product>({
    table: 'Products',
    filters: [{ field: 'category', operator: 'eq', value: category }],
    limit,
    sort: [{ field: 'rating', direction: 'desc' }],
  });
};

/**
 * 价格范围筛选
 */
export const getProductsByPriceRange = (
  minPrice: number,
  maxPrice: number,
  limit = 50
): Promise<QueryResponse<Product>> => {
  return query<Product>({
    table: 'Products',
    filters: [
      { field: 'discounted_price', operator: 'gte', value: minPrice },
      { field: 'discounted_price', operator: 'lte', value: maxPrice },
    ],
    limit,
    sort: [{ field: 'discounted_price', direction: 'asc' }],
  });
};

/**
 * 高评分商品
 */
export const getTopRatedProducts = (
  minRating = 4.5,
  limit = 20
): Promise<QueryResponse<Product>> => {
  return query<Product>({
    table: 'Products',
    filters: [{ field: 'rating', operator: 'gte', value: minRating }],
    limit,
    sort: [{ field: 'rating', direction: 'desc' }],
  });
};

/**
 * 高折扣商品
 */
export const getHighDiscountProducts = (
  minDiscount = 50,
  limit = 50
): Promise<QueryResponse<Product>> => {
  return query<Product>({
    table: 'Products',
    filters: [
      { field: 'discount_percentage', operator: 'gte', value: minDiscount },
    ],
    limit,
    sort: [{ field: 'discount_percentage', direction: 'desc' }],
  });
};

// ============ 聚合 API ============

/**
 * 按类别聚合统计
 */
export const aggregateByCategory = (): Promise<AggregationResponse> => {
  return api.post(`/api/databases/${USER_ID}/${DB_NAME}/query/aggregate`, {
    table: 'Products',
    group_by: 'category',
    aggregations: {
      total_count: { field: '*', operation: 'count' },
      avg_price: { field: 'discounted_price', operation: 'avg' },
      avg_rating: { field: 'rating', operation: 'avg' },
    },
  });
};

/**
 * 价格分布统计
 */
export const getPriceDistribution = () => {
  return api.post(`/api/databases/${USER_ID}/${DB_NAME}/query/aggregate`, {
    table: 'Products',
    group_by: 'category',
    aggregations: {
      min_price: { field: 'discounted_price', operation: 'min' },
      max_price: { field: 'discounted_price', operation: 'max' },
      avg_price: { field: 'discounted_price', operation: 'avg' },
    },
  });
};

/**
 * 计数查询
 */
export const countProducts = (filters?: QueryRequest['filters']): Promise<CountResponse> => {
  return api.post(`/api/databases/${USER_ID}/${DB_NAME}/query/count`, {
    table: 'Products',
    filters,
  });
};

/**
 * 自定义聚合查询
 */
export const customAggregate = (params: AggregationRequest): Promise<AggregationResponse> => {
  return api.post(`/api/databases/${USER_ID}/${DB_NAME}/query/aggregate`, params);
};

export default api;
