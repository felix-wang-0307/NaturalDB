import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Typography,
  Spin,
  Card,
  Row,
  Col,
  Image,
  Tag,
  Divider,
  Button,
  Space,
  Rate,
  List,
  Avatar,
  Empty,
  Statistic,
  Alert,
  Descriptions,
  Badge
} from 'antd';
import {
  ArrowLeftOutlined,
  ShoppingCartOutlined,
  StarOutlined,
  UserOutlined,
  TagOutlined,
  PercentageOutlined
} from '@ant-design/icons';
import { query } from '../services/api';
import type { Product, Review } from '../types';
import './ProductDetailPage.less';

const { Title, Text, Paragraph } = Typography;

const ProductDetailPage = () => {
  const { productId } = useParams<{ productId: string }>();
  const navigate = useNavigate();
  const [product, setProduct] = useState<Product | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);
  const [reviewsLoading, setReviewsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (productId) {
      loadProduct();
      loadReviews();
    }
  }, [productId]);

  const loadProduct = async () => {
    try {
      setLoading(true);
      setError(null);
      
      if (!productId) {
        setError('Product ID is required');
        return;
      }
      
      // Query product by product_id
      const response = await query<Product>({
        table: 'Products',
        filters: [{ field: 'product_id', operator: 'eq', value: productId }],
        limit: 1
      });

      if (response.results && response.results.length > 0) {
        setProduct(response.results[0]);
      } else {
        setError('Product not found');
      }
    } catch (err) {
      console.error('Error loading product:', err);
      setError('Failed to load product details');
    } finally {
      setLoading(false);
    }
  };

  const loadReviews = async () => {
    try {
      setReviewsLoading(true);
      
      if (!productId) return;
      
      const response = await query<Review>({
        table: 'Reviews',
        filters: [{ field: 'product_id', operator: 'eq', value: productId }],
        limit: 50,
        sort: [{ field: 'id', direction: 'asc' }]
      });

      if (response.results) {
        setReviews(response.results);
      }
    } catch (err) {
      console.error('Error loading reviews:', err);
    } finally {
      setReviewsLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <Spin size="large" tip="Loading product details..." />
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="error-container">
        <Alert
          message="Error"
          description={error || 'Product not found'}
          type="error"
          showIcon
        />
        <Button
          type="primary"
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/products')}
          style={{ marginTop: 16 }}
        >
          Back to Products
        </Button>
      </div>
    );
  }

  const categoryDisplay = product.category
    .replace(/([A-Z])/g, ' $1')
    .trim()
    .replace(/^./, str => str.toUpperCase());

  const savings = product.actual_price - product.discounted_price;
  const savingsPercentage = ((savings / product.actual_price) * 100).toFixed(0);

  return (
    <div className="product-detail-page">
      <div className="page-header">
        <Button
          type="text"
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/products')}
          size="large"
        >
          Back to Products
        </Button>
      </div>

      <Card className="product-card">
        <Row gutter={[32, 32]}>
          {/* Product Image */}
          <Col xs={24} md={10} lg={8}>
            <div className="product-image-container">
              <Image
                src={product.img_link}
                alt={product.product_name}
                className="product-image"
                fallback="data:image/png;base64,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"
              />
              {product.discount_percentage > 0 && (
                <Badge.Ribbon
                  text={`${product.discount_percentage}% OFF`}
                  color="red"
                  className="discount-ribbon"
                />
              )}
            </div>
          </Col>

          {/* Product Info */}
          <Col xs={24} md={14} lg={16}>
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              {/* Title and Category */}
              <div>
                <Tag color="blue" icon={<TagOutlined />}>{categoryDisplay}</Tag>
                <Title level={2} style={{ marginTop: 8, marginBottom: 0 }}>
                  {product.product_name}
                </Title>
              </div>

              {/* Rating */}
              <div className="rating-section">
                <Space size="large">
                  <div>
                    <Rate disabled allowHalf value={product.rating} />
                    <Text strong style={{ marginLeft: 8 }}>
                      {product.rating.toFixed(1)}
                    </Text>
                  </div>
                  <Text type="secondary">
                    {product.rating_count.toLocaleString()} ratings
                  </Text>
                </Space>
              </div>

              <Divider style={{ margin: '12px 0' }} />

              {/* Price Section */}
              <div className="price-section">
                <Space size="large" align="start">
                  <Statistic
                    title="Price"
                    value={product.discounted_price}
                    prefix="$"
                    precision={2}
                    valueStyle={{ color: '#cf1322', fontSize: '32px', fontWeight: 'bold' }}
                  />
                  {product.discount_percentage > 0 && (
                    <div>
                      <div>
                        <Text delete type="secondary" style={{ fontSize: '18px' }}>
                          ${product.actual_price.toFixed(2)}
                        </Text>
                      </div>
                      <Tag color="success" icon={<PercentageOutlined />} style={{ marginTop: 4 }}>
                        Save ${savings.toFixed(2)} ({savingsPercentage}%)
                      </Tag>
                    </div>
                  )}
                </Space>
              </div>

              <Divider style={{ margin: '12px 0' }} />

              {/* About Product */}
              {product.about_product && (
                <div className="about-section">
                  <Title level={4}>About this product</Title>
                  <Paragraph>
                    {product.about_product.split('|').map((point, index) => (
                      <div key={index} style={{ marginBottom: 8 }}>
                        • {point.trim()}
                      </div>
                    ))}
                  </Paragraph>
                </div>
              )}

              {/* Actions */}
              <Space size="middle">
                <Button
                  type="primary"
                  size="large"
                  icon={<ShoppingCartOutlined />}
                  onClick={() => window.open(product.product_link, '_blank')}
                >
                  View on Amazon
                </Button>
              </Space>

              {/* Product Details */}
              <Descriptions title="Product Details" bordered column={1} size="small">
                <Descriptions.Item label="Product ID">{product.product_id}</Descriptions.Item>
                <Descriptions.Item label="Category">
                  {product.category_path ? product.category_path.join(' > ') : categoryDisplay}
                </Descriptions.Item>
                <Descriptions.Item label="Discount">{product.discount_percentage}%</Descriptions.Item>
                <Descriptions.Item label="Rating Count">
                  {product.rating_count.toLocaleString()}
                </Descriptions.Item>
              </Descriptions>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Reviews Section */}
      <Card
        title={
          <Space>
            <StarOutlined style={{ fontSize: '24px', color: '#faad14' }} />
            <Title level={3} style={{ margin: 0 }}>Customer Reviews</Title>
            {reviews.length > 0 && (
              <Tag color="blue">{reviews.length} reviews</Tag>
            )}
          </Space>
        }
        className="reviews-card"
        style={{ marginTop: 24 }}
      >
        {reviewsLoading ? (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <Spin size="large" tip="Loading reviews..." />
          </div>
        ) : reviews.length === 0 ? (
          <Empty
            description="No reviews yet"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        ) : (
          <List
            itemLayout="vertical"
            size="large"
            dataSource={reviews}
            pagination={{
              pageSize: 10,
              showTotal: (total) => `Total ${total} reviews`,
              showSizeChanger: false
            }}
            renderItem={(review) => (
              <List.Item
                key={review.review_id}
                className="review-item"
              >
                <List.Item.Meta
                  avatar={
                    <Avatar
                      icon={<UserOutlined />}
                      size="large"
                      style={{ backgroundColor: '#1890ff' }}
                    />
                  }
                  title={
                    <Space direction="vertical" size={0}>
                      <Text strong style={{ fontSize: '16px' }}>
                        {review.review_title}
                      </Text>
                      <Text type="secondary" style={{ fontSize: '14px' }}>
                        by {review.user_name}
                      </Text>
                    </Space>
                  }
                />
                {review.review_content && (
                  <Paragraph
                    style={{
                      marginTop: 8,
                      fontSize: '14px',
                      color: 'rgba(0, 0, 0, 0.65)'
                    }}
                  >
                    {review.review_content}
                  </Paragraph>
                )}
              </List.Item>
            )}
          />
        )}
      </Card>
    </div>
  );
};

export default ProductDetailPage;
