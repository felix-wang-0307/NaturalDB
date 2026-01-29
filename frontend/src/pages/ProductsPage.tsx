import { useEffect, useState, useCallback, useMemo } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import {
  Row,
  Col,
  Card,
  Input,
  Select,
  Slider,
  Button,
  Tag,
  Pagination,
  Spin,
  Empty,
  Space,
  Typography,
} from 'antd';
import {
  SearchOutlined,
  FilterOutlined,
  ClearOutlined,
  StarOutlined,
} from '@ant-design/icons';
import { getProducts } from '../services/api';
import type { Product, QueryFilter } from '../types';
import {
  formatPrice,
  formatNumber,
  getRatingColor,
  debounce,
} from '../utils/helpers';
import './ProductsPage.less';

const { Title } = Typography;
const { Option } = Select;

const ProductsPage = () => {
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(false);
  const [products, setProducts] = useState<Product[]>([]);
  const [total, setTotal] = useState(0);
  
  // Filter states (used for API calls)
  const [searchText, setSearchText] = useState('');
  const [debouncedSearchText, setDebouncedSearchText] = useState('');
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [priceRange, setPriceRange] = useState<[number, number]>([0, 100000]);
  const [debouncedPriceRange, setDebouncedPriceRange] = useState<[number, number]>([0, 100000]);
  const [minRating, setMinRating] = useState(0);
  const [debouncedMinRating, setDebouncedMinRating] = useState(0);
  const [minDiscount, setMinDiscount] = useState(0);
  const [debouncedMinDiscount, setDebouncedMinDiscount] = useState(0);
  const [sortBy, setSortBy] = useState<string>('rating_desc');
  
  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 24;

  // Create debounced setters
  const debouncedSetSearchText = useMemo(
    () => debounce((value: string) => setDebouncedSearchText(value), 500),
    []
  );

  const debouncedSetPriceRange = useMemo(
    () => debounce((value: [number, number]) => setDebouncedPriceRange(value), 300),
    []
  );

  const debouncedSetMinRating = useMemo(
    () => debounce((value: number) => setDebouncedMinRating(value), 300),
    []
  );

  const debouncedSetMinDiscount = useMemo(
    () => debounce((value: number) => setDebouncedMinDiscount(value), 300),
    []
  );

  // Initialize filters from URL params
  useEffect(() => {
    const urlMinRating = searchParams.get('minRating');
    const urlMinDiscount = searchParams.get('minDiscount');
    
    if (urlMinRating) {
      setMinRating(parseFloat(urlMinRating));
    }
    
    if (urlMinDiscount) {
      setMinDiscount(parseFloat(urlMinDiscount));
    }
  }, [searchParams]);

  const categories = [
    { value: 'USBCables', label: 'USB Cables' },
    { value: 'Smartphones', label: 'Smartphones' },
    { value: 'SmartWatches', label: 'Smart Watches' },
    { value: 'SmartTelevisions', label: 'Smart Televisions' },
    { value: 'In-Ear', label: 'In-Ear Headphones' },
    { value: 'RemoteControls', label: 'Remote Controls' },
    { value: 'MixerGrinders', label: 'Mixer Grinders' },
    { value: 'Mice', label: 'Mice' },
    { value: 'DryIrons', label: 'Dry Irons' },
    { value: 'InstantWaterHeaters', label: 'Instant Water Heaters' },
    { value: 'HDMICables', label: 'HDMI Cables' },
    { value: 'ElectricKettles', label: 'Electric Kettles' },
    { value: 'WallChargers', label: 'Wall Chargers' },
    { value: 'WirelessUSBAdapters', label: 'Wireless USB Adapters' },
    { value: 'PowerBanks', label: 'Power Banks' },
    { value: 'Keyboards', label: 'Keyboards' },
    { value: 'Headphones', label: 'Headphones' },
    { value: 'ScreenProtectors', label: 'Screen Protectors' },
  ];

  const loadProducts = useCallback(async () => {
    try {
      setLoading(true);

      // Build filters
      const filters: QueryFilter[] = [];

      if (debouncedSearchText) {
        filters.push({
          field: 'product_name',
          operator: 'contains',
          value: debouncedSearchText,
        });
      }

      if (selectedCategories.length > 0) {
        filters.push({
          field: 'category',
          operator: 'in',
          value: selectedCategories,
        });
      }

      // 只在用户设置了非默认值时才添加price filters
      if (debouncedPriceRange[0] > 0) {
        filters.push({
          field: 'discounted_price',
          operator: 'gte',
          value: debouncedPriceRange[0],
        });
      }

      if (debouncedPriceRange[1] < 100000) {
        filters.push({
          field: 'discounted_price',
          operator: 'lte',
          value: debouncedPriceRange[1],
        });
      }

      if (debouncedMinRating > 0) {
        filters.push({
          field: 'rating',
          operator: 'gte',
          value: debouncedMinRating,
        });
      }

      if (debouncedMinDiscount > 0) {
        filters.push({
          field: 'discount_percentage',
          operator: 'gte',
          value: debouncedMinDiscount,
        });
      }

      // Build sort
      const [field, direction] = sortBy.split('_');
      const sort = [{ field, direction: direction as 'asc' | 'desc' }];

      const response = await getProducts({
        filters,
        sort,
        limit: pageSize,
        skip: (currentPage - 1) * pageSize,
      });

      setProducts(response.results);
      setTotal(response.total ?? response.count);  // Use total if available, fallback to count
    } catch (error) {
      console.error('Failed to load products:', error);
    } finally {
      setLoading(false);
    }
  }, [debouncedSearchText, selectedCategories, debouncedPriceRange, debouncedMinRating, debouncedMinDiscount, sortBy, currentPage]);

  useEffect(() => {
    loadProducts();
  }, [loadProducts]);

  const handleSearch = (value: string) => {
    setSearchText(value);
    debouncedSetSearchText(value);
    setCurrentPage(1);
  };

  const handleReset = () => {
    setSearchText('');
    setDebouncedSearchText('');
    setSelectedCategories([]);
    setPriceRange([0, 100000]);
    setDebouncedPriceRange([0, 100000]);
    setMinRating(0);
    setDebouncedMinRating(0);
    setMinDiscount(0);
    setDebouncedMinDiscount(0);
    setSortBy('rating_desc');
    setCurrentPage(1);
  };

  return (
    <div className="products-page page-container">
      <div className="page-header">
        <Title level={2}>Product Catalog</Title>
        <div className="header-stats">
          Showing {products.length} of {total} products
          {(minRating > 0 || minDiscount > 0) && (
            <Tag color="blue" style={{ marginLeft: 8 }}>
              {minRating > 0 && `Rating ≥ ${minRating}`}
              {minRating > 0 && minDiscount > 0 && ' & '}
              {minDiscount > 0 && `Discount ≥ ${minDiscount}%`}
            </Tag>
          )}
        </div>
      </div>

      <Row gutter={24}>
        {/* Filters Sidebar */}
        <Col xs={24} md={6}>
          <div className="filter-sidebar">
            <div className="filter-header">
              <Title level={4}>
                <FilterOutlined /> Filters
              </Title>
              <Button
                size="small"
                icon={<ClearOutlined />}
                onClick={handleReset}
              >
                Reset
              </Button>
            </div>

            <div className="filter-section">
              <div className="filter-title">Search</div>
              <Input
                placeholder="Search products..."
                prefix={<SearchOutlined />}
                value={searchText}
                onChange={(e) => handleSearch(e.target.value)}
                allowClear
              />
            </div>

            <div className="filter-section">
              <div className="filter-title">Category</div>
              <Select
                mode="multiple"
                style={{ width: '100%' }}
                placeholder="All Categories"
                value={selectedCategories}
                onChange={(value) => {
                  setSelectedCategories(value);
                  setCurrentPage(1);
                }}
                allowClear
                maxTagCount="responsive"
              >
                {categories.map((cat) => (
                  <Option key={cat.value} value={cat.value}>
                    {cat.label}
                  </Option>
                ))}
              </Select>
            </div>

            <div className="filter-section">
              <div className="filter-title">
                Price Range: {formatPrice(priceRange[0])} - {formatPrice(priceRange[1])}
              </div>
              <Slider
                range
                min={0}
                max={100000}
                step={100}
                value={priceRange}
                onChange={(value) => {
                  const newValue = value as [number, number];
                  setPriceRange(newValue);
                  debouncedSetPriceRange(newValue);
                  setCurrentPage(1);
                }}
              />
            </div>

            <div className="filter-section">
              <div className="filter-title">
                Minimum Rating: {minRating.toFixed(1)}★
              </div>
              <Slider
                min={0}
                max={5}
                step={0.1}
                value={minRating}
                onChange={(value) => {
                  setMinRating(value);
                  debouncedSetMinRating(value);
                  setCurrentPage(1);
                }}
                marks={{
                  0: '0',
                  2.5: '2.5',
                  5: '5',
                }}
                tooltip={{
                  formatter: (value) => `${value?.toFixed(1)}★`,
                }}
              />
            </div>

            <div className="filter-section">
              <div className="filter-title">Minimum Discount: {minDiscount}%</div>
              <Slider
                min={0}
                max={100}
                value={minDiscount}
                onChange={(value) => {
                  setMinDiscount(value);
                  debouncedSetMinDiscount(value);
                  setCurrentPage(1);
                }}
              />
            </div>
          </div>
        </Col>

        {/* Products Grid */}
        <Col xs={24} md={18}>
          <div className="products-container">
            <div className="products-toolbar">
              <div className="sort-controls">
                <span>Sort by:</span>
                <Select
                  value={sortBy}
                  onChange={(value) => {
                    setSortBy(value);
                    setCurrentPage(1);
                  }}
                  style={{ width: 200 }}
                >
                  <Option value="rating_desc">Rating: High to Low</Option>
                  <Option value="rating_asc">Rating: Low to High</Option>
                  <Option value="discounted_price_asc">Price: Low to High</Option>
                  <Option value="discounted_price_desc">Price: High to Low</Option>
                  <Option value="discount_percentage_desc">Discount: High to Low</Option>
                </Select>
              </div>
            </div>

            {loading ? (
              <div className="loading-container">
                <Spin size="large" />
              </div>
            ) : products.length === 0 ? (
              <Empty description="No products found" />
            ) : (
              <>
                <Row gutter={[16, 16]}>
                  {products.map((product) => (
                    <Col key={product.id} xs={24} sm={12} lg={8} xl={6}>
                      <Link to={`/products/${product.product_id}`}>
                        <Card
                          hoverable
                          className="product-card"
                          cover={
                            <div className="product-image">
                              <img
                                alt={product.product_name}
                                src={product.img_link}
                                onError={(e) => {
                                  (e.target as HTMLImageElement).src =
                                    'https://via.placeholder.com/300x300?text=No+Image';
                                }}
                              />
                              {product.discount_percentage >= 50 && (
                                <div className="discount-badge">
                                  -{product.discount_percentage}%
                                </div>
                              )}
                            </div>
                          }
                        >
                          <div className="product-title">{product.product_name}</div>
                          <div className="product-category">{product.category}</div>
                          <div className="product-price">
                            <span className="current-price">
                              {formatPrice(product.discounted_price)}
                            </span>
                            <span className="original-price">
                              {formatPrice(product.actual_price)}
                            </span>
                          </div>
                          <Space size="small" wrap>
                            <Tag
                              color={getRatingColor(product.rating)}
                              icon={<StarOutlined />}
                            >
                              {product.rating}
                            </Tag>
                            <Tag color="blue">
                              {formatNumber(product.rating_count)} reviews
                            </Tag>
                          </Space>
                        </Card>
                      </Link>
                    </Col>
                  ))}
                </Row>

                <div className="pagination-container">
                  <Pagination
                    current={currentPage}
                    pageSize={pageSize}
                    total={total}
                    onChange={(page) => setCurrentPage(page)}
                    showSizeChanger={false}
                    showTotal={(total) => `Total ${total} items`}
                  />
                </div>
              </>
            )}
          </div>
        </Col>
      </Row>
    </div>
  );
};

export default ProductsPage;
