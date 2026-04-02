const express = require('express');
const cors = require('cors');
const net = require('net');

// 富途OpenD配置
const FUTU_OPEND_HOST = '127.0.0.1';
const FUTU_OPEND_PORT = 11111;
const APP_ID = 'futunnative';

// 检查端口是否开放
function checkPort(host, port) {
  return new Promise((resolve) => {
    const socket = new net.Socket();
    socket.setTimeout(2000);

    socket.on('connect', () => {
      socket.destroy();
      resolve(true);
    });

    socket.on('timeout', () => {
      socket.destroy();
      resolve(false);
    });

    socket.on('error', () => {
      socket.destroy();
      resolve(false);
    });

    socket.connect(port, host);
  });
}

// 富途 OpenD TCP 客户端
class FutuClient {
  constructor() {
    this.socket = null;
    this.connected = false;
    this.requestId = 1;
    this.callbacks = new Map();
    this.buffer = Buffer.alloc(0);
  }

  // 连接 OpenD
  async connect(retries = 3) {
    for (let i = 0; i < retries; i++) {
      console.log(`[FutuClient] 尝试连接 OpenD (${i + 1}/${retries})...`);

      try {
        const connected = await this.connectSocket();
        if (connected) {
          console.log('[FutuClient] ✓ OpenD 连接成功');
          this.connected = true;
          return true;
        }
      } catch (error) {
        console.log(`[FutuClient] ✗ 连接失败: ${error.message}`);
      }

      if (i < retries - 1) {
        console.log('3秒后重试...');
        await this.sleep(3000);
      }
    }

    console.log('⚠ OpenD 连接失败，将使用模拟数据');
    return false;
  }

  // 建立 TCP Socket 连接
  connectSocket() {
    return new Promise((resolve, reject) => {
      this.socket = new net.Socket();
      this.socket.setTimeout(10000);

      this.socket.on('connect', () => {
        console.log('[FutuClient] TCP 连接已建立，发送握手...');
        this.sendHandshake().then(() => {
          resolve(true);
        }).catch((err) => {
          reject(err);
        });
      });

      this.socket.on('data', (data) => {
        this.handleData(data);
      });

      this.socket.on('error', (err) => {
        console.log('[FutuClient] Socket 错误:', err.message);
        reject(err);
      });

      this.socket.on('timeout', () => {
        console.log('[FutuClient] 连接超时');
        reject(new Error('Connection timeout'));
      });

      this.socket.connect(FUTU_OPEND_PORT, FUTU_OPEND_HOST);
    });
  }

  // 处理接收到的数据
  handleData(data) {
    this.buffer = Buffer.concat([this.buffer, data]);

    // 解析包：4字节长度 + 包体
    while (this.buffer.length >= 4) {
      const bodyLen = this.buffer.readUInt32BE(4);
      const totalLen = 4 + bodyLen;

      if (this.buffer.length < totalLen) {
        break; // 数据不完整，等待更多数据
      }

      const packet = this.buffer.slice(4, totalLen);
      this.buffer = this.buffer.slice(totalLen);

      this.parsePacket(packet);
    }
  }

  // 解析数据包
  parsePacket(packet) {
    try {
      // 包头 2字节 + 2字节serial_no + 4字节proto_id + 2字节包类型
      if (packet.length < 10) return;

      const protoId = packet.readUInt32BE(6);
      const serialNo = packet.readUInt32BE(2);
      const bodyLen = packet.length - 10;
      const body = bodyLen > 0 ? packet.slice(10) : null;

      // 检查是否是心跳包
      if (protoId === 0 && bodyLen === 0) {
        // 发送心跳响应
        return;
      }

      // 检查是否有等待的回调
      if (this.callbacks.has(serialNo)) {
        const callback = this.callbacks.get(serialNo);
        this.callbacks.delete(serialNo);

        if (body && body.length > 0) {
          try {
            // 尝试解析 JSON
            const jsonStr = body.toString('utf8').replace(/[\x00-\x1F]/g, '');
            const response = JSON.parse(jsonStr);
            callback(null, response);
          } catch (e) {
            // 解析失败，传递原始数据
            callback(null, { raw: body.toString('base64') });
          }
        } else {
          callback(null, {});
        }
      }
    } catch (error) {
      console.error('[FutuClient] 解析数据包错误:', error.message);
    }
  }

  // 发送握手请求
  async sendHandshake() {
    return new Promise((resolve, reject) => {
      const serialNo = this.requestId++;
      const body = JSON.stringify({
        'WebSocketProtocolVer': 1,
        'AutoReconnect': true,
        'AppID': APP_ID,
        'AppVersion': '1.0'
      });

      const packet = this.buildPacket(1001, serialNo, body);

      this.callbacks.set(serialNo, (err, response) => {
        if (err) {
          reject(err);
        } else {
          console.log('[FutuClient] ✓ 握手成功');
          resolve(response);
        }
      });

      this.socket.write(packet);

      // 10秒超时
      setTimeout(() => {
        if (this.callbacks.has(serialNo)) {
          this.callbacks.delete(serialNo);
          reject(new Error('Handshake timeout'));
        }
      }, 10000);

      this.socket.once('data', (data) => {
        // 握手响应会在下一个数据包里
      });
    });
  }

  // 构建数据包
  buildPacket(protoId, serialNo, body) {
    const bodyBuffer = Buffer.from(body, 'utf8');
    const header = Buffer.alloc(10);
    header.writeUInt16BE(1, 0); // 包类型：请求
    header.writeUInt32BE(serialNo, 2);
    header.writeUInt32BE(protoId, 6);

    const length = header.length + bodyBuffer.length;
    const packet = Buffer.alloc(4 + length);
    packet.writeUInt32BE(length, 0);
    header.copy(packet, 4);
    bodyBuffer.copy(packet, 4 + header.length);

    return packet;
  }

  // 发送请求
  async sendRequest(protoId, body) {
    if (!this.connected || !this.socket) {
      throw new Error('Not connected');
    }

    return new Promise((resolve, reject) => {
      const serialNo = this.requestId++;
      const bodyStr = typeof body === 'string' ? body : JSON.stringify(body);
      const packet = this.buildPacket(protoId, serialNo, bodyStr);

      this.callbacks.set(serialNo, (err, response) => {
        if (err) reject(err);
        else resolve(response);
      });

      this.socket.write(packet);

      // 10秒超时
      setTimeout(() => {
        if (this.callbacks.has(serialNo)) {
          this.callbacks.delete(serialNo);
          reject(new Error('Request timeout'));
        }
      }, 10000);
    });
  }

  // 获取美股实时报价 (proto_id: 2201)
  async getMarketSnapshot(codes) {
    try {
      console.log(`[FutuClient] 获取报价: ${codes.join(', ')}`);

      // 格式化股票代码：US.NVDA
      const formattedCodes = codes.map(code => `US.${code}`);

      const body = JSON.stringify({
        'securityList': formattedCodes
      });

      const response = await this.sendRequest(2201, body);

      if (response && response.s2c) {
        const data = response.s2c;
        if (data.marketSnapshotData && data.marketSnapshotData.length > 0) {
          return data.marketSnapshotData.map(item => {
            const code = item.code || '';
            const symbol = code.replace('US.', '');
            const curPrice = item.curPrice || 0;
            const lastClose = item.lastClose || 0;
            const change = lastClose > 0 ? ((curPrice - lastClose) / lastClose) * 100 : 0;

            return {
              symbol: symbol,
              code: symbol,
              name: ALL_STOCKS.find(s => s.code === symbol)?.name || symbol,
              currentPrice: curPrice,
              previousClose: lastClose,
              change: parseFloat(change.toFixed(2)),
              changeText: change >= 0 ? `+${change.toFixed(2)}%` : `${change.toFixed(2)}%`
            };
          });
        }
      }

      console.log('[FutuClient] ⚠ 无报价数据返回');
      return null;
    } catch (error) {
      console.error('[FutuClient] 获取报价失败:', error.message);
      return null;
    }
  }

  // 获取K线数据 (proto_id: 2204)
  async getHistoryKline(symbol, period) {
    try {
      console.log(`[FutuClient] 获取K线: ${symbol} (${period})`);

      // 转换时间段
      const periodMap = {
        '1D': { timeFrame: 'TK_1M', count: 1440 },
        '1W': { timeFrame: 'TK_5M', count: 672 },
        '1M': { timeFrame: 'TK_1H', count: 600 },
        '3M': { timeFrame: 'TK_1H', count: 1800 }
      };
      const config = periodMap[period] || periodMap['1D'];

      const body = JSON.stringify({
        'security': `US.${symbol}`,
        'timeFrame': config.timeFrame,
        'maxCount': config.count,
        'nextReqKey': ''
      });

      const response = await this.sendRequest(2204, body);

      if (response && response.s2c && response.s2c.klines) {
        const klines = response.s2c.klines;
        if (klines.length >= 2) {
          const firstLine = klines[0].split(',');
          const lastLine = klines[klines.length - 1].split(',');

          const startPrice = parseFloat(firstLine[2]); // 收盘价
          const endPrice = parseFloat(lastLine[2]);

          const change = ((endPrice - startPrice) / startPrice) * 100;

          return {
            symbol: symbol,
            startPrice: startPrice,
            endPrice: endPrice,
            change: parseFloat(change.toFixed(2))
          };
        }
      }

      return null;
    } catch (error) {
      console.error(`[FutuClient] 获取K线失败 (${symbol}):`, error.message);
      return null;
    }
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  disconnect() {
    if (this.socket) {
      this.socket.destroy();
      this.socket = null;
    }
    this.connected = false;
  }
}

const app = express();
app.use(cors());
app.use(express.json());

// 存储热门板块数据（带实时价格）
let hotSectorsData = null;
let lastUpdateTime = null;

// 所有需要查询的股票代码
const ALL_STOCKS = [
  // AI & Tech
  { code: 'QQQ', name: 'Invesco QQQ Trust', sector: 'AI & Tech' },
  { code: 'NVDA', name: 'NVIDIA', sector: 'AI & Tech' },
  { code: 'MSFT', name: 'Microsoft', sector: 'AI & Tech' },
  { code: 'GOOGL', name: 'Alphabet', sector: 'AI & Tech' },
  // Semiconductor
  { code: 'SMH', name: 'VanEck Semiconductor', sector: 'Semiconductor' },
  { code: 'AMD', name: 'AMD', sector: 'Semiconductor' },
  { code: 'INTC', name: 'Intel', sector: 'Semiconductor' },
  { code: 'ASML', name: 'ASML Holding', sector: 'Semiconductor' },
  // EV & Energy
  { code: 'ICLN', name: 'iShares Clean Energy', sector: 'EV & Energy' },
  { code: 'TSLA', name: 'Tesla', sector: 'EV & Energy' },
  { code: 'ENPH', name: 'Enphase Energy', sector: 'EV & Energy' },
  { code: 'FSLR', name: 'First Solar', sector: 'EV & Energy' },
  // Healthcare
  { code: 'XLV', name: 'Health Care SPDR', sector: 'Healthcare' },
  { code: 'JNJ', name: 'Johnson & Johnson', sector: 'Healthcare' },
  { code: 'UNH', name: 'UnitedHealth', sector: 'Healthcare' },
  { code: 'LLY', name: 'Eli Lilly', sector: 'Healthcare' },
  // Finance
  { code: 'XLF', name: 'Financials SPDR', sector: 'Finance' },
  { code: 'JPM', name: 'JPMorgan Chase', sector: 'Finance' },
  { code: 'BAC', name: 'Bank of America', sector: 'Finance' },
  { code: 'GS', name: 'Goldman Sachs', sector: 'Finance' },
];

// 板块配置
const SECTOR_CONFIG = [
  {
    id: 'AI_Tech',
    name: 'AI & Tech',
    nameCn: '人工智能',
    stocks: ['QQQ', 'NVDA', 'MSFT', 'GOOGL']
  },
  {
    id: 'Semiconductor',
    name: 'Semiconductor',
    nameCn: '半导体',
    stocks: ['SMH', 'AMD', 'INTC', 'ASML']
  },
  {
    id: 'EV_Energy',
    name: 'EV & Energy',
    nameCn: '新能源',
    stocks: ['ICLN', 'TSLA', 'ENPH', 'FSLR']
  },
  {
    id: 'Healthcare',
    name: 'Healthcare',
    nameCn: '医疗健康',
    stocks: ['XLV', 'JNJ', 'UNH', 'LLY']
  },
  {
    id: 'Finance',
    name: 'Finance',
    nameCn: '金融',
    stocks: ['XLF', 'JPM', 'BAC', 'GS']
  }
];

// 创建富途客户端实例
const futuClient = new FutuClient();

// 生成模拟涨跌幅数据（根据时间段）
function generateMockData(period = '1D') {
  // 不同时间段的基础涨跌幅范围
  const periodConfig = {
    '1D': { min: -2, max: 3, volatility: 0.3 },     // 一天: -2% ~ +3%
    '1W': { min: -5, max: 15, volatility: 1 },      // 一周: -5% ~ +15%
    '1M': { min: -10, max: 30, volatility: 2.5 },   // 一月: -10% ~ +30%
    '3M': { min: -20, max: 50, volatility: 4 }      // 三月: -20% ~ +50%
  };

  const config = periodConfig[period] || periodConfig['1W'];

  const sectors = SECTOR_CONFIG.map(sector => {
    const stocks = sector.stocks.map(code => {
      const stockInfo = ALL_STOCKS.find(s => s.code === code);
      // 根据时间段生成涨跌幅
      const range = config.max - config.min;
      const change = (Math.random() * range + config.min) * config.volatility;
      const roundedChange = parseFloat(change.toFixed(2));
      return {
        code: code,
        name: stockInfo ? stockInfo.name : code,
        change: roundedChange,
        changeText: roundedChange >= 0 ? `+${roundedChange}%` : `${roundedChange}%`
      };
    });

    // 板块平均涨跌幅
    const avgChange = stocks.reduce((sum, s) => sum + s.change, 0) / stocks.length;

    return {
      id: sector.id,
      name: sector.name,
      nameCn: sector.nameCn,
      trend: avgChange >= 0 ? 'up' : 'down',
      change: avgChange >= 0 ? `+${avgChange.toFixed(1)}%` : `${avgChange.toFixed(1)}%`,
      avgChange: avgChange,
      etf: stocks[0],
      stocks: stocks.slice(1)
    };
  });

  // 按涨跌幅排序
  sectors.sort((a, b) => b.avgChange - a.avgChange);

  return sectors;
}

// 路由：获取热门板块数据
app.get('/api/hot-sectors', async (req, res) => {
  try {
    const period = req.query.period || '1D'; // 1D, 1W, 1M, 3M

    // 如果有缓存且更新时间在1分钟内，直接返回
    const cacheKey = `hotSectors_${period}`;
    const cachedData = global[cacheKey];
    const cachedTime = global[`${cacheKey}_time`];

    if (cachedData && cachedTime && (Date.now() - cachedTime) < 60 * 1000) {
      return res.json({
        success: true,
        connected: futuClient.connected,
        data: cachedData,
        updateTime: cachedTime,
        source: 'cache',
        period: period
      });
    }

    let sectorsData;

    if (futuClient.connected) {
      console.log(`[API] 从富途 OpenD 获取 ${period} 真实数据...`);

      // 获取所有股票代码
      const codes = ALL_STOCKS.map(s => s.code);

      try {
        // 获取实时快照（当日涨跌幅）
        const quotes = await futuClient.getMarketSnapshot(codes);

        if (quotes && quotes.length > 0) {
          console.log(`[API] ✓ 获取到 ${quotes.length} 只股票报价`);

          sectorsData = SECTOR_CONFIG.map(sector => {
            const stockData = sector.stocks.map(code => {
              const quote = quotes.find(q => q.code === code);
              if (quote) {
                return {
                  code: code,
                  name: quote.name || code,
                  change: quote.change,
                  changeText: quote.changeText
                };
              } else {
                return null;
              }
            }).filter(s => s !== null);

            if (stockData.length === 0) return null;

            const avgChange = stockData.reduce((sum, s) => sum + s.change, 0) / stockData.length;

            return {
              id: sector.id,
              name: sector.name,
              nameCn: sector.nameCn,
              trend: avgChange >= 0 ? 'up' : 'down',
              change: avgChange >= 0 ? `+${avgChange.toFixed(1)}%` : `${avgChange.toFixed(1)}%`,
              avgChange: avgChange,
              etf: stockData[0],
              stocks: stockData.slice(1)
            };
          }).filter(s => s !== null);

          sectorsData.sort((a, b) => b.avgChange - a.avgChange);
          console.log(`[API] ✓ 富途 OpenD 数据加载成功 (${period})`);
        } else {
          console.log(`[API] ⚠ 富途 OpenD 无报价数据，使用模拟数据`);
          sectorsData = generateMockData(period);
        }
      } catch (apiError) {
        console.error(`[API] 富途 API 调用失败:`, apiError.message);
        sectorsData = generateMockData(period);
      }
    } else {
      console.log(`[API] ⚠ OpenD 未连接，使用模拟数据 (${period})`);
      sectorsData = generateMockData(period);
    }

    // 缓存数据
    global[cacheKey] = sectorsData;
    global[`${cacheKey}_time`] = Date.now();

    res.json({
      success: true,
      connected: futuClient.connected,
      data: sectorsData,
      updateTime: Date.now(),
      source: futuClient.connected ? 'futu_opend' : 'mock',
      period: period
    });

  } catch (error) {
    console.error('API Error:', error);
    const period = req.query.period || '1D';
    sectorsData = generateMockData(period);
    res.json({
      success: false,
      error: error.message,
      data: sectorsData,
      updateTime: Date.now(),
      source: 'mock_fallback',
      period: period
    });
  }
});

// 路由：获取单个股票报价
app.get('/api/quote/:code', async (req, res) => {
  const { code } = req.params;

  try {
    if (futuClient.connected) {
      const quotes = await futuClient.getQuotes([code]);
      return res.json({
        success: true,
        data: quotes && quotes.length > 0 ? quotes[0] : null
      });
    }

    res.json({
      success: false,
      error: 'OpenD not connected',
      data: null
    });

  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// 路由：健康检查
app.get('/api/health', async (req, res) => {
  const portOpen = await checkPort(FUTU_OPEND_HOST, FUTU_OPEND_PORT);
  res.json({
    status: 'ok',
    futuConnected: futuClient.connected,
    portOpen: portOpen,
    serverTime: new Date().toISOString(),
    timestamp: Date.now()
  });
});

// 路由：测试富途 OpenD API
app.get('/api/test-futu', async (req, res) => {
  const symbol = req.query.symbol || 'NVDA';
  try {
    // 测试获取快照
    const snapshotData = await futuClient.getMarketSnapshot([symbol]);
    // 测试获取K线
    const klineData = await futuClient.getHistoryKline(symbol, '1D');

    res.json({
      symbol: symbol,
      connected: futuClient.connected,
      snapshot: snapshotData,
      kline: klineData,
      serverTime: new Date().toISOString()
    });
  } catch (error) {
    res.status(500).json({
      error: error.message,
      symbol: symbol,
      connected: futuClient.connected
    });
  }
});
      stooq: stooqData,
      serverTime: new Date().toISOString()
    });
  } catch (error) {
    res.status(500).json({
      error: error.message,
      symbol: symbol,
      period: period
    });
  }
});

// 路由：检测OpenD端口状态
app.get('/api/check-port', async (req, res) => {
  const portOpen = await checkPort(FUTU_OPEND_HOST, FUTU_OPEND_PORT);
  res.json({
    port: FUTU_OPEND_PORT,
    host: FUTU_OPEND_HOST,
    open: portOpen,
    message: portOpen ? '端口开放，OpenD API 服务可能已启用' : '端口未开放，OpenD API 服务未启用'
  });
});

// 启动服务器
const PORT = 3000;

async function start() {
  console.log('=================================');
  console.log('   Stock API Server Starting...');
  console.log('=================================');

  // 尝试连接OpenD
  const connected = await futuClient.connect();

  if (connected) {
    console.log('✓ Futu OpenD connected successfully');
  } else {
    console.log('⚠ Futu OpenD not available, using mock data');
    console.log('  Please make sure OpenD is running and logged in');
  }

  // 启动Express服务器
  app.listen(PORT, () => {
    console.log('');
    console.log('=================================');
    console.log(`   Server running on port ${PORT}`);
    console.log(`   OpenD Status: ${connected ? '✓ Connected' : '✗ Disconnected'}`);
    console.log('=================================');
    console.log('');
    console.log('API Endpoints:');
    console.log(`  GET http://localhost:${PORT}/api/hot-sectors`);
    console.log(`  GET http://localhost:${PORT}/api/quote/:code`);
    console.log(`  GET http://localhost:${PORT}/api/health`);
    console.log('');
  });
}

// 优雅关闭
process.on('SIGINT', () => {
  console.log('\nShutting down...');
  futuClient.disconnect();
  process.exit(0);
});

start();
