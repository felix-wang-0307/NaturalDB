// NaturalDB Frontend Type Definitions

export interface Product {
  id: string;
  product_id: string;
  product_name: string;
  category: string;
  category_path: string[];
  discounted_price: number;
  actual_price: number;
  discount_percentage: number;
  rating: number;
  rating_count: number;
  about_product: string;
  img_link: string;
  product_link: string;
}

export interface Review {
  id: string;
  review_id: string;
  product_id: string;
  user_id: string;
  user_name: string;
  review_title: string;
  review_content: string;
}

export interface User {
  id: string;
  user_id: string;
  user_name: string;
}

export interface Category {
  id: string;
  category_id: string;
  category_name: string;
}

export interface QueryFilter {
  field: string;
  operator: 'eq' | 'ne' | 'gt' | 'gte' | 'lt' | 'lte' | 'in' | 'nin' | 'contains';
  value: string | number | boolean | string[] | number[];
}

export interface QuerySort {
  field: string;
  direction: 'asc' | 'desc';
}

export interface QueryRequest {
  table: string;
  filters?: QueryFilter[];
  sort?: QuerySort[];
  limit?: number;
  skip?: number;
  project?: string[];
}

export interface QueryResponse<T = unknown> {
  success: boolean;
  user_id: string;
  db_name: string;
  table: string;
  count: number;
  results: T[];
}

export interface AggregationRequest {
  table: string;
  group_by: string;
  aggregations: {
    [key: string]: {
      field: string;
      operation: 'sum' | 'avg' | 'count' | 'min' | 'max';
    };
  };
  filters?: QueryFilter[];
}

export interface AggregationResult {
  [key: string]: string | number;
}

export interface AggregationResponse {
  success: boolean;
  user_id: string;
  db_name: string;
  table: string;
  group_by: string;
  count: number;
  results: AggregationResult[];
}

export interface CountResponse {
  success: boolean;
  user_id: string;
  db_name: string;
  table: string;
  count: number;
}

export interface PriceRange {
  min: number;
  max: number;
}

export interface FilterOptions {
  categories: string[];
  priceRange: PriceRange;
  minRating: number;
  minDiscount: number;
  searchText: string;
}
