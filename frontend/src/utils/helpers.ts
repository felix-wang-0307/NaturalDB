/**
 * 格式化价格显示
 */
export const formatPrice = (price: number): string => {
  return `₹${price.toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
};

/**
 * 格式化数字（添加千分位）
 */
export const formatNumber = (num: number): string => {
  return num.toLocaleString('en-IN');
};

/**
 * 计算节省金额
 */
export const calculateSavings = (actualPrice: number, discountedPrice: number): number => {
  return actualPrice - discountedPrice;
};

/**
 * 截断文本
 */
export const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};

/**
 * 获取评分颜色
 */
export const getRatingColor = (rating: number): string => {
  if (rating >= 4.5) return '#52c41a'; // green
  if (rating >= 4.0) return '#faad14'; // yellow
  if (rating >= 3.0) return '#ff7a45'; // orange
  return '#f5222d'; // red
};

/**
 * 获取折扣标签颜色
 */
export const getDiscountColor = (discount: number): string => {
  if (discount >= 70) return '#f5222d'; // red
  if (discount >= 50) return '#fa8c16'; // orange
  if (discount >= 30) return '#faad14'; // yellow
  return '#52c41a'; // green
};

/**
 * 提取类别路径的主类别
 */
export const getMainCategory = (categoryPath: string[]): string => {
  return categoryPath && categoryPath.length > 0 ? categoryPath[0] : 'Unknown';
};

/**
 * 提取类别路径的子类别
 */
export const getSubCategory = (categoryPath: string[]): string => {
  return categoryPath && categoryPath.length > 1 
    ? categoryPath[categoryPath.length - 1] 
    : 'Unknown';
};

/**
 * 格式化类别路径为面包屑
 */
export const formatCategoryPath = (categoryPath: string[]): string => {
  return categoryPath ? categoryPath.join(' > ') : 'Unknown';
};

/**
 * 防抖函数
 */
export const debounce = <T extends (...args: unknown[]) => void>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: ReturnType<typeof setTimeout> | null = null;
  
  return function executedFunction(...args: Parameters<T>) {
    const later = () => {
      timeout = null;
      func(...args);
    };
    
    if (timeout !== null) {
      clearTimeout(timeout);
    }
    timeout = setTimeout(later, wait);
  };
};

/**
 * 生成唯一 ID
 */
export const generateId = (): string => {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
};

/**
 * 安全获取嵌套对象属性
 */
export const getNestedValue = (obj: Record<string, unknown>, path: string): unknown => {
  return path.split('.').reduce((acc: unknown, part: string) => {
    if (acc && typeof acc === 'object' && part in acc) {
      return (acc as Record<string, unknown>)[part];
    }
    return undefined;
  }, obj);
};

/**
 * 排序数组
 */
export const sortArray = <T>(
  array: T[],
  key: keyof T,
  direction: 'asc' | 'desc' = 'asc'
): T[] => {
  return [...array].sort((a, b) => {
    const aVal = a[key];
    const bVal = b[key];
    
    if (aVal < bVal) return direction === 'asc' ? -1 : 1;
    if (aVal > bVal) return direction === 'asc' ? 1 : -1;
    return 0;
  });
};

/**
 * 分组数组
 */
export const groupBy = <T>(array: T[], key: keyof T): Record<string, T[]> => {
  return array.reduce((result, item) => {
    const groupKey = String(item[key]);
    if (!result[groupKey]) {
      result[groupKey] = [];
    }
    result[groupKey].push(item);
    return result;
  }, {} as Record<string, T[]>);
};
