import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Row,
  Col,
  Card,
  Statistic,
  Button,
  Typography,
  Space,
  Tag,
  Spin,
} from 'antd';
import {
  ShoppingOutlined,
  StarOutlined,
  PercentageOutlined,
  DatabaseOutlined,
  RightOutlined,
} from '@ant-design/icons';
import { getProducts, countProducts } from '../services/api';
import type { Product } from '../types';
import { formatPrice, getRatingColor } from '../utils/helpers';
import './HomePage.less';

const { Title, Paragraph } = Typography;

const HomePage = () => {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalProducts: 0,
    highRated: 0,
    highDiscount: 0,
  });
  const [featuredProducts, setFeaturedProducts] = useState<Product[]>([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);

      // 获取统计数据
      const [total, highRatedRes, highDiscountRes] = await Promise.all([
        countProducts(),
        countProducts([{ field: 'rating', operator: 'gte', value: 4.5 }]),
        countProducts([{ field: 'discount_percentage', operator: 'gte', value: 60 }]),
      ]);

      setStats({
        totalProducts: total.count || 0,
        highRated: highRatedRes.count || 0,
        highDiscount: highDiscountRes.count || 0,
      });

      // 获取精选商品（高评分 + 高折扣）
      const featured = await getProducts({
        filters: [
          { field: 'rating', operator: 'gte', value: 4.3 },
          { field: 'discount_percentage', operator: 'gte', value: 50 },
        ],
        sort: [{ field: 'rating', direction: 'desc' }],
        limit: 8,
      });

      setFeaturedProducts(featured.results);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="home-page">
      <div className="hero-section">
        <div className="hero-content">
          <Title level={1}>Welcome to NaturalDB Demo</Title>
          <Paragraph className="hero-description">
            Experience a powerful NoSQL database system with natural language query capabilities.
            Browse our Amazon product catalog with advanced filtering, sorting, and analytics.
          </Paragraph>
          <Space size="large">
            <Link to="/products">
              <Button type="primary" size="large" icon={<ShoppingOutlined />}>
                Browse Products
              </Button>
            </Link>
            <Link to="/query-builder">
              <Button size="large" icon={<DatabaseOutlined />}>
                Try Query Builder
              </Button>
            </Link>
          </Space>
        </div>
      </div>

      {loading ? (
        <div className="loading-container">
          <Spin size="large" />
        </div>
      ) : (
        <>
          {/* Statistics */}
          <div className="stats-section">
            <Title level={2}>Database Statistics</Title>
            <Row gutter={[24, 24]}>
              <Col xs={24} sm={12} lg={8}>
                <Link to="/products">
                  <Card hoverable className="stat-card">
                    <Statistic
                      title="Total Products"
                      value={stats.totalProducts}
                      prefix={<ShoppingOutlined />}
                      valueStyle={{ color: '#1890ff' }}
                    />
                    <div className="card-hint">Click to browse all products</div>
                  </Card>
                </Link>
              </Col>
              <Col xs={24} sm={12} lg={8}>
                <Link to="/products">
                  <Card hoverable className="stat-card">
                    <Statistic
                      title="Highly Rated (≥4.5★)"
                      value={stats.highRated}
                      prefix={<StarOutlined />}
                      valueStyle={{ color: '#52c41a' }}
                    />
                    <div className="card-hint">Click to view top-rated products</div>
                  </Card>
                </Link>
              </Col>
              <Col xs={24} sm={12} lg={8}>
                <Link to="/products">
                  <Card hoverable className="stat-card">
                    <Statistic
                      title="Big Discounts (≥60%)"
                      value={stats.highDiscount}
                      prefix={<PercentageOutlined />}
                      valueStyle={{ color: '#f5222d' }}
                    />
                    <div className="card-hint">Click to see best deals</div>
                  </Card>
                </Link>
              </Col>
            </Row>
          </div>

          {/* Featured Products */}
          <div className="featured-section">
            <div className="section-header">
              <Title level={2}>Featured Products</Title>
              <Link to="/products">
                <Button type="link" icon={<RightOutlined />} iconPosition="end">
                  View All
                </Button>
              </Link>
            </div>

            <Row gutter={[16, 16]}>
              {featuredProducts.map((product) => (
                <Col key={product.id} xs={24} sm={12} md={8} lg={6}>
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
                        </div>
                      }
                    >
                      <div className="product-title">{product.product_name}</div>
                      <div className="product-price">
                        <span className="current-price">
                          {formatPrice(product.discounted_price)}
                        </span>
                        <span className="original-price">
                          {formatPrice(product.actual_price)}
                        </span>
                      </div>
                      <Space direction="vertical" size="small" style={{ width: '100%' }}>
                        <div className="product-meta">
                          <Tag
                            color={getRatingColor(product.rating)}
                            icon={<StarOutlined />}
                          >
                            {product.rating}
                          </Tag>
                          <Tag color="red">{product.discount_percentage}% OFF</Tag>
                        </div>
                      </Space>
                    </Card>
                  </Link>
                </Col>
              ))}
            </Row>
          </div>

          {/* Features */}
          <div className="features-section">
            <Title level={2}>Key Features</Title>
            <Row gutter={[24, 24]}>
              <Col xs={24} md={8}>
                <Card className="feature-card">
                  <DatabaseOutlined className="feature-icon" />
                  <Title level={4}>NoSQL Power</Title>
                  <Paragraph>
                    Custom-built NoSQL database with JSON storage, supporting complex queries,
                    filtering, and aggregations.
                  </Paragraph>
                </Card>
              </Col>
              <Col xs={24} md={8}>
                <Card className="feature-card">
                  <ShoppingOutlined className="feature-icon" />
                  <Title level={4}>Rich E-commerce Data</Title>
                  <Paragraph>
                    1,300+ products with detailed information including ratings, reviews,
                    categories, and pricing from Amazon.
                  </Paragraph>
                </Card>
              </Col>
              <Col xs={24} md={8}>
                <Card className="feature-card">
                  <StarOutlined className="feature-icon" />
                  <Title level={4}>Advanced Queries</Title>
                  <Paragraph>
                    Build complex queries with visual query builder. Filter by price, rating,
                    discount, and more!
                  </Paragraph>
                </Card>
              </Col>
            </Row>
          </div>
        </>
      )}
    </div>
  );
};

export default HomePage;
