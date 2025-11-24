import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Layout, Menu, Typography } from 'antd';
import {
  HomeOutlined,
  ShoppingOutlined,
  DashboardOutlined,
  SearchOutlined,
  DatabaseOutlined,
} from '@ant-design/icons';
import HomePage from './pages/HomePage';
import ProductsPage from './pages/ProductsPage';
import ProductDetailPage from './pages/ProductDetailPage';
import QueryBuilderPage from './pages/QueryBuilderPage';
import DashboardPage from './pages/DashboardPage';
import './App.less';

const { Header, Content, Footer } = Layout;
const { Title } = Typography;

function App() {
  return (
    <Router>
      <Layout className="app-layout">
        <Header className="app-header">
          <div className="logo">
            <DatabaseOutlined className="logo-icon" />
            <Title level={3} className="logo-text">
              NaturalDB Demo
            </Title>
          </div>
          <Menu
            theme="dark"
            mode="horizontal"
            defaultSelectedKeys={['home']}
            className="main-menu"
          >
            <Menu.Item key="home" icon={<HomeOutlined />}>
              <Link to="/">Home</Link>
            </Menu.Item>
            <Menu.Item key="products" icon={<ShoppingOutlined />}>
              <Link to="/products">Products</Link>
            </Menu.Item>
            <Menu.Item key="dashboard" icon={<DashboardOutlined />}>
              <Link to="/dashboard">Dashboard</Link>
            </Menu.Item>
            <Menu.Item key="query" icon={<SearchOutlined />}>
              <Link to="/query-builder">Query Builder</Link>
            </Menu.Item>
          </Menu>
        </Header>

        <Content className="app-content">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/products" element={<ProductsPage />} />
            <Route path="/products/:productId" element={<ProductDetailPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/query-builder" element={<QueryBuilderPage />} />
          </Routes>
        </Content>

        <Footer className="app-footer">
          <div className="footer-content">
            <div>
              <strong>NaturalDB</strong> - A Natural-Language-Driven NoSQL Database System
            </div>
            <div>
              USC DSCI-551 Project © 2024 | Built with React + TypeScript + Ant Design
            </div>
          </div>
        </Footer>
      </Layout>
    </Router>
  );
}

export default App;
