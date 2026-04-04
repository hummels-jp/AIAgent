const express = require('express');
const cors = require('cors');
const { spawn, exec } = require('child_process');
const path = require('path');

const app = express();
app.use(cors());
app.use(express.json());

// 服务器路径
const SERVER_PATH = path.join(__dirname, 'server.js');
const WORKING_DIR = __dirname;

// 进程管理
let serverProcess = null;
let isShuttingDown = false;

// 富途 OpenD 配置
const FUTU_OPEND_HOST = '127.0.0.1';
const FUTU_OPEND_PORT = 11111;

// Python 脚本路径
const PYTHON_SCRIPT = path.join(__dirname, 'futu_service.py');

// 所有需要查询的股票代码
const ALL_STOCKS = [
  { code: 'QQQ', name: 'Invesco QQQ Trust', sector: 'AI & Tech' },
  { code: 'NVDA', name: 'NVIDIA', sector: 'AI & Tech' },
  { code: 'MSFT', name: 'Microsoft', sector: 'AI & Tech' },
  { code: 'GOOGL', name: 'Alphabet', sector: 'AI & Tech' },
  { code: 'SMH', name: 'VanEck Semiconductor', sector: 'Semiconductor' },
  { code: 'AMD', name: 'AMD', sector: 'Semiconductor' },
  { code: 'INTC', name: 'Intel', sector: 'Semiconductor' },
  { code: 'ASML', name: 'ASML Holding', sector: 'Semiconductor' },
  { code: 'ICLN', name: 'iShares Clean Energy', sector: 'EV & Energy' },
  { code: 'TSLA', name: 'Tesla', sector: 'EV & Energy' },
  { code: 'ENPH', name: 'Enphase Energy', sector: 'EV & Energy' },
  { code: 'FSLR', name: 'First Solar', sector: 'EV & Energy' },
  { code: 'XLV', name: 'Health Care SPDR', sector: 'Healthcare' },
  { code: 'JNJ', name: 'Johnson & Johnson', sector: 'Healthcare' },
  { code: 'UNH', name: 'UnitedHealth', sector: 'Healthcare' },
  { code: 'LLY', name: 'Eli Lilly', sector: 'Healthcare' },
  { code: 'XLF', name: 'Financials SPDR', sector: 'Finance' },
  { code: 'JPM', name: 'JPMorgan Chase', sector: 'Finance' },
  { code: 'BAC', name: 'Bank of America', sector: 'Finance' },
  { code: 'GS', name: 'Goldman Sachs', sector: 'Finance' },
];

// 板块配置
const SECTOR_CONFIG = [
  { id: 'AI_Tech', name: 'AI & Tech', nameCn: '人工智能', stocks: ['QQQ', 'NVDA', 'MSFT', 'GOOGL'] },
  { id: 'Semiconductor', name: 'Semiconductor', nameCn: '半导体', stocks: ['SMH', 'AMD', 'INTC', 'ASML'] },
  { id: 'EV_Energy', name: 'EV & Energy', nameCn: '新能源', stocks: ['ICLN', 'TSLA', 'ENPH', 'FSLR'] },
  { id: 'Healthcare', name: 'Healthcare', nameCn: '医疗健康', stocks: ['XLV', 'JNJ', 'UNH', 'LLY'] },
  { id: 'Finance', name: 'Finance', nameCn: '金融', stocks: ['XLF', 'JPM', 'BAC', 'GS'] },
  { id: 'ECommerce', name: 'E-Commerce', nameCn: '电商零售', stocks: ['AMZN', 'WMT', 'TGT', 'COST'] },
  { id: 'CloudComputing', name: 'Cloud Computing', nameCn: '云计算', stocks: ['CRM', 'NOW', 'SNOW', 'WDAY'] },
  { id: 'Cybersecurity', name: 'Cybersecurity', nameCn: '网络安全', stocks: ['PANW', 'CRWD', 'ZS', 'OKTA'] },
  { id: 'Biotech', name: 'Biotech', nameCn: '生物科技', stocks: ['XBI', 'MRNA', 'REGN', 'VRTX'] },
  { id: 'RealEstate', name: 'Real Estate', nameCn: '房地产', stocks: ['VNQ', 'PLD', 'AMT', 'EQIX'] }
];

// 调用 Python 脚本获取富途数据
function getFutuData(action, options = {}) {
  return new Promise((resolve, reject) => {
    const args = [
      PYTHON_SCRIPT,
      '--action', action,
      '--market', options.market || 'HK'
    ];
    
    if (options.start) {
      args.push('--start', options.start);
    }
    if (options.end) {
      args.push('--end', options.end);
    }
    if (options.period) {
      args.push('--period', options.period);
    }
    if (options.minCap) {
      args.push('--min-cap', options.minCap.toString());
    }
    if (options.top) {
      args.push('--top', options.top.toString());
    }
    if (options.group) {
      args.push('--group', options.group);
    }
    if (options.page) {
      args.push('--page', options.page.toString());
    }
    if (options.pageSize) {
      args.push('--page-size', options.pageSize.toString());
    }
    if (options.codes) {
      args.push('--codes', options.codes);
    }

    console.log(`[FutuService] 调用 Python 脚本: action=${action}`);
    
    // Windows 上使用 python，Linux/Mac 上使用 python3
    const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
    const python = spawn(pythonCmd, args);
    
    let output = '';
    let errorOutput = '';

    python.stdout.on('data', (data) => {
      output += data.toString();
    });

    python.stderr.on('data', (data) => {
      errorOutput += data.toString();
    });

    python.on('close', (code) => {
      console.log(`[FutuService] Python 进程退出，code=${code}`);
      
      if (code === 0) {
        try {
          // 提取 JSON（可能有日志输出）
          const lines = output.split('\n').filter(l => l.trim());
          const jsonLine = lines.find(l => l.trim().startsWith('{'));
          
          if (jsonLine) {
            const result = JSON.parse(jsonLine);
            console.log(`[FutuService] 解析成功，connected=${result.connected}, data=${result.data?.length || 0}条`);
            resolve(result);
          } else {
            reject(new Error(`未找到 JSON 输出: ${output.substring(0, 200)}`));
          }
        } catch (e) {
          console.log(`[FutuService] JSON 解析失败: ${e.message}`);
          console.log(`[FutuService] 输出内容: ${output.substring(0, 500)}`);
          reject(new Error(`JSON 解析失败: ${e.message}`));
        }
      } else {
        console.log(`[FutuService] 执行失败: ${errorOutput}`);
        reject(new Error(`Python 脚本执行失败 (code: ${code}): ${errorOutput}`));
      }
    });

    python.on('error', (err) => {
      console.log(`[FutuService] 无法启动 Python: ${err.message}`);
      reject(new Error(`无法启动 Python: ${err.message}`));
    });
  });
}

// 生成模拟涨跌幅数据（仅在富途未连接时使用）
function generateMockData(period = '1D') {
  const periodConfig = {
    '1D': { min: -3, max: 5 },
    '1W': { min: -8, max: 12 },
    '1M': { min: -15, max: 25 },
    '3M': { min: -25, max: 45 }
  };

  const config = periodConfig[period] || periodConfig['1W'];

  const sectors = SECTOR_CONFIG.map(sector => {
    const stocks = sector.stocks.map(code => {
      const stockInfo = ALL_STOCKS.find(s => s.code === code);
      const range = config.max - config.min;
      const change = config.min + Math.random() * range;
      const roundedChange = parseFloat(change.toFixed(2));
      return {
        code: code,
        name: stockInfo ? stockInfo.name : code,
        change: roundedChange,
        changeText: roundedChange >= 0 ? `+${roundedChange}%` : `${roundedChange}%`
      };
    });

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

  sectors.sort((a, b) => b.avgChange - a.avgChange);
  return sectors;
}

// 获取股票涨跌幅（调用富途API）
async function getStockChangeRates(period = '1D') {
  const daysMap = { '1D': 1, '1W': 7, '1M': 30, '3M': 90 };
  const days = daysMap[period] || 7;

  return new Promise((resolve, reject) => {
    const args = [
      'python',
      PYTHON_SCRIPT,
      '--action', 'stock-changes',
      '--days', days.toString()
    ];

    const python = spawn(args[0], args.slice(1), { cwd: WORKING_DIR });

    let output = '';
    let errorOutput = '';

    python.stdout.on('data', (data) => {
      output += data.toString();
    });

    python.stderr.on('data', (data) => {
      errorOutput += data.toString();
    });

    python.on('close', (code) => {
      if (code === 0 && output) {
        try {
          const result = JSON.parse(output);
          resolve(result);
        } catch (e) {
          console.log(`[StockChange] 解析失败: ${output}`);
          reject(new Error('解析失败'));
        }
      } else {
        reject(new Error(`获取失败: ${errorOutput}`));
      }
    });
  });
}

// 生成板块数据（优先使用富途真实数据）
async function generateSectorData(period = '1D', useRealData = false) {
  let stockChanges = {};

  // 如果使用真实数据，尝试获取
  if (useRealData) {
    try {
      const result = await getStockChangeRates(period);
      if (result.success && result.data) {
        stockChanges = result.data;
        console.log(`[Sectors] 使用真实数据: ${Object.keys(stockChanges).length} 只股票`);
      }
    } catch (e) {
      console.log(`[Sectors] 获取真实数据失败: ${e.message}，使用模拟数据`);
    }
  }

  const sectors = SECTOR_CONFIG.map(sector => {
    const stocks = sector.stocks.map(code => {
      const stockInfo = ALL_STOCKS.find(s => s.code === code);
      let change;
      
      // 使用真实数据或模拟数据
      if (stockChanges[code] !== undefined) {
        change = stockChanges[code];
      } else {
        // 模拟数据作为备用
        const periodConfig = {
          '1D': { min: -3, max: 5 },
          '1W': { min: -8, max: 12 },
          '1M': { min: -15, max: 25 },
          '3M': { min: -25, max: 45 }
        };
        const config = periodConfig[period] || periodConfig['1W'];
        const range = config.max - config.min;
        change = config.min + Math.random() * range;
        change = parseFloat(change.toFixed(2));
      }

      return {
        code: code,
        name: stockInfo ? stockInfo.name : code,
        change: change,
        changeText: change >= 0 ? `+${change}%` : `${change}%`
      };
    });

    const avgChange = stocks.reduce((sum, s) => sum + s.change, 0) / stocks.length;

    return {
      id: sector.id,
      name: sector.name,
      nameCn: sector.nameCn,
      trend: avgChange >= 0 ? 'up' : 'down',
      change: avgChange >= 0 ? `+${avgChange.toFixed(1)}%` : `${avgChange.toFixed(1)}%`,
      avgChange: parseFloat(avgChange.toFixed(2)),
      etf: stocks[0],
      stocks: stocks.slice(1)
    };
  });

  sectors.sort((a, b) => b.avgChange - a.avgChange);
  return sectors;
}

// 生成模拟交易记录
function generateMockTrades(period) {
  const now = new Date();
  const trades = [];

  const mockStocks = [
    { code: '00700', name: '腾讯控股' },
    { code: '09988', name: '阿里巴巴' },
    { code: 'TSLA', name: '特斯拉' },
    { code: 'NVDA', name: '英伟达' },
    { code: 'AAPL', name: '苹果' },
    { code: 'MSFT', name: '微软' },
    { code: 'GOOGL', name: '谷歌' }
  ];

  const countMap = { 'today': 3, '1w': 6, '1m': 12 };
  const count = countMap[period] || 3;

  for (let i = 0; i < count; i++) {
    const stock = mockStocks[Math.floor(Math.random() * mockStocks.length)];
    const direction = Math.random() > 0.5 ? '买入' : '卖出';
    const quantity = Math.floor(Math.random() * 500 + 100);
    const price = Math.random() * 500 + 50;
    const amount = quantity * price;

    const randomHours = Math.floor(Math.random() * 8 + 9);
    const tradeTime = new Date(now.getTime() - Math.random() * 24 * 60 * 60 * 1000);
    tradeTime.setHours(randomHours, Math.floor(Math.random() * 60), 0);

    trades.push({
      time: tradeTime.toISOString(),
      code: stock.code,
      name: stock.name,
      direction: direction,
      directionRaw: direction === '买入' ? 'BUY' : 'SELL',
      quantity: quantity,
      price: parseFloat(price.toFixed(2)),
      amount: parseFloat(amount.toFixed(2)),
      orderID: `ORD${Date.now()}${i}`
    });
  }

  trades.sort((a, b) => new Date(b.time) - new Date(a.time));
  return trades;
}

// 辅助函数：格式化日期为 YYYY-MM-DD
function formatDate(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

// 检查富途连接状态
function checkFutuConnection() {
  return new Promise((resolve, reject) => {
    const net = require('net');
    const client = new net.Socket();
    
    client.setTimeout(2000);
    
    client.on('connect', () => {
      client.destroy();
      resolve({ futuConnected: true });
    });
    
    client.on('timeout', () => {
      client.destroy();
      resolve({ futuConnected: false });
    });
    
    client.on('error', () => {
      client.destroy();
      resolve({ futuConnected: false });
    });
    
    client.connect(FUTU_OPEND_PORT, FUTU_OPEND_HOST);
  });
}

// ==================== API 路由 ====================

// 路由：获取热门板块数据
app.get('/api/hot-sectors', async (req, res) => {
  try {
    const period = req.query.period || '1D';
    const cacheKey = `hotSectors_${period}`;
    const cachedData = global[cacheKey];
    const cachedTime = global[`${cacheKey}_time`];

    // 检查富途连接状态
    let isFutuConnected = false;
    try {
      const healthResult = await checkFutuConnection();
      isFutuConnected = healthResult.futuConnected;
    } catch (e) {
      console.log(`[Sectors] 富途连接检查失败: ${e.message}`);
    }

    if (cachedData && cachedTime && (Date.now() - cachedTime) < 60 * 1000) {
      return res.json({
        success: true,
        connected: isFutuConnected,
        data: cachedData,
        updateTime: cachedTime,
        source: 'cache',
        period: period
      });
    }

    // 尝试获取真实数据，如果失败则使用模拟数据
    const sectorsData = await generateSectorData(period, isFutuConnected);

    global[cacheKey] = sectorsData;
    global[`${cacheKey}_time`] = Date.now();

    res.json({
      success: true,
      connected: true,
      data: sectorsData,
      updateTime: Date.now(),
      source: 'mock',
      period: period
    });

  } catch (error) {
    console.error('API Error:', error);
    res.json({
      success: false,
      error: error.message,
      data: generateMockData(req.query.period || '1D'),
      updateTime: Date.now(),
      source: 'mock_fallback'
    });
  }
});

// 路由：健康检查
app.get('/api/health', async (req, res) => {
  res.json({
    status: 'ok',
    openDHost: FUTU_OPEND_HOST,
    openDPort: FUTU_OPEND_PORT,
    serverTime: new Date().toISOString(),
    timestamp: Date.now()
  });
});

// 路由：检测OpenD连接状态
app.get('/api/check-port', async (req, res) => {
  try {
    const result = await getFutuData('today');
    res.json({
      port: FUTU_OPEND_PORT,
      host: FUTU_OPEND_HOST,
      connected: result.connected,
      message: result.connected
        ? 'OpenD 连接成功！'
        : 'OpenD 连接失败',
      instructions: [
        '1. 确保富途 OpenD 已启动并登录',
        '2. 确保 OpenD 中已启用 API 服务',
        '3. 确认端口号为 11111'
      ]
    });
  } catch (error) {
    res.json({
      port: FUTU_OPEND_PORT,
      host: FUTU_OPEND_HOST,
      connected: false,
      message: `连接失败: ${error.message}`,
      instructions: [
        '1. 确保富途 OpenD 已启动并登录',
        '2. 确保 OpenD 中已启用 API 服务',
        '3. 确认端口号为 11111'
      ]
    });
  }
});

// 路由：获取交易记录
app.get('/api/trade-history', async (req, res) => {
  try {
    const period = req.query.period || 'today';
    const market = req.query.market || 'HK';

    console.log(`[API] 获取交易记录: period=${period}, market=${market}`);

    let trades = [];
    let connected = false;

    try {
      const result = await getFutuData(period, { market, start: '', end: '' });
      
      if (result.connected && result.success) {
        connected = true;
        trades = result.data;
        console.log(`[API] ✓ 从 OpenD 获取到 ${trades.length} 条记录`);
      } else {
        console.log(`[API] ⚠ OpenD 获取失败: ${result.error || '未知错误'}`);
      }
    } catch (error) {
      console.log(`[API] ⚠ 调用 Python 失败: ${error.message}`);
    }

    res.json({
      success: true,
      connected: connected,
      data: trades,
      period: period,
      market: market,
      updateTime: Date.now(),
      total: trades.length,
      note: connected
        ? (trades.length > 0 ? '数据来自富途 OpenD' : '今日暂无交易记录')
        : 'OpenD 未连接，请检查 OpenD 是否启动'
    });

  } catch (error) {
    console.error('[API] 获取交易记录失败:', error);
    res.status(200).json({
      success: false,
      error: error.message,
      data: [],
      connected: false,
      note: '获取数据失败: ' + error.message
    });
  }
});

// 路由：获取持仓
app.get('/api/positions', async (req, res) => {
  try {
    const result = await getFutuData('positions');
    
    res.json({
      success: result.success,
      connected: result.connected,
      data: result.data || [],
      error: result.error,
      updateTime: Date.now()
    });

  } catch (error) {
    console.error('[API] 获取持仓失败:', error);
    res.status(500).json({
      success: false,
      error: error.message,
      data: [],
      connected: false
    });
  }
});

// 路由：获取 VIX 数据
app.get('/api/vix', async (req, res) => {
  try {
    const https = require('https');

    const options = {
      hostname: 'query1.finance.yahoo.com',
      path: '/v8/finance/chart/%5EVIX?interval=1d&range=1d',
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json'
      }
    };

    https.get(options, (apiRes) => {
      let data = '';

      apiRes.on('data', (chunk) => {
        data += chunk;
      });

      apiRes.on('end', () => {
        try {
          const json = JSON.parse(data);
          const result = json.chart?.result?.[0];

          if (!result) {
            return res.json({
              success: false,
              error: '无法获取 VIX 数据',
              value: null,
              change: null,
              previousClose: null
            });
          }

          const vixValue = result.meta.regularMarketPrice;
          // 尝试多个字段获取前收盘价
          const previousClose = result.meta.previousClose || 
            (result.indicators?.quote?.[0]?.close?.[result.indicators.quote[0].close.length - 2]) ||
            vixValue;
          const change = previousClose && previousClose > 0 
            ? ((vixValue - previousClose) / previousClose * 100).toFixed(2)
            : 0;

          res.json({
            success: true,
            value: vixValue,
            previousClose: previousClose,
            change: parseFloat(change)
          });
        } catch (e) {
          res.json({
            success: false,
            error: '解析 VIX 数据失败',
            value: null,
            change: null
          });
        }
      });
    }).on('error', (err) => {
      res.json({
        success: false,
        error: err.message,
        value: null,
        change: null
      });
    });

  } catch (error) {
    res.json({
      success: false,
      error: error.message,
      value: null,
      change: null
    });
  }
});

// 路由：启动服务
app.post('/api/server/start', async (req, res) => {
  try {
    console.log('[Server] 收到启动服务请求');

    // 检查是否已经在运行
    if (serverProcess && !serverProcess.killed) {
      return res.json({
        success: true,
        message: '服务已在运行中',
        running: true
      });
    }

    // 启动服务
    serverProcess = spawn('node', [SERVER_PATH], {
      cwd: WORKING_DIR,
      detached: true,
      stdio: 'ignore'
    });

    serverProcess.unref();

    console.log('[Server] 服务启动中...');

    setTimeout(() => {
      res.json({
        success: true,
        message: '服务启动成功',
        running: true
      });
    }, 1000);

  } catch (error) {
    console.error('[Server] 启动失败:', error);
    res.json({
      success: false,
      error: error.message
    });
  }
});

// 路由：重启服务
app.post('/api/server/restart', async (req, res) => {
  try {
    console.log('[Server] 收到重启服务请求');

    // 清理旧进程
    if (serverProcess && !serverProcess.killed) {
      console.log('[Server] 关闭旧服务...');
      serverProcess.kill();
      serverProcess = null;
    }

    // 等待进程关闭
    await new Promise(resolve => setTimeout(resolve, 500));

    // 启动新服务
    console.log('[Server] 启动新服务...');

    const newProcess = spawn('node', [SERVER_PATH], {
      cwd: WORKING_DIR,
      detached: true,
      stdio: 'ignore'
    });

    newProcess.unref();
    serverProcess = newProcess;

    console.log('[Server] 服务重启成功');

    res.json({
      success: true,
      message: '服务重启成功',
      running: true
    });

  } catch (error) {
    console.error('[Server] 重启失败:', error);
    res.json({
      success: false,
      error: error.message
    });
  }
});

// 路由：获取热门股票（涨幅最大的10只，市值5000亿+）
app.get('/api/hot-stocks', async (req, res) => {
  try {
    const period = req.query.period || '1M';
    const minMarketCap = parseInt(req.query.minCap) || 5000;
    const topCount = parseInt(req.query.top) || 10;

    console.log(`[HotStocks] 获取热门股票: period=${period}, minCap=${minMarketCap}, top=${topCount}`);

    // 调用 Python 富途服务获取数据
    const futuData = await getFutuData('hot-stocks', {
      period: period,
      minCap: minMarketCap,
      top: topCount
    });

    if (futuData.success && futuData.data && futuData.data.length > 0) {
      console.log(`[HotStocks] 从 Futu 获取 ${futuData.data.length} 只热门股票`);
      res.json({
        success: true,
        data: futuData.data,
        period: period,
        source: 'futu',
        connected: futuData.connected,
        updateTime: Date.now()
      });
    } else {
      console.log(`[HotStocks] Futu 数据为空，返回模拟数据`);
      res.json({
        success: true,
        data: generateMockHotStocks(),
        period: period,
        source: 'mock',
        updateTime: Date.now()
      });
    }

  } catch (error) {
    console.error('[API] 获取热门股票失败:', error);
    res.json({
      success: false,
      error: error.message,
      data: generateMockHotStocks(),
      updateTime: Date.now()
    });
  }
});

// 路由：获取自选股票列表（市值1000亿+）
app.get('/api/watchlist', async (req, res) => {
  try {
    const minMarketCap = parseInt(req.query.minCap) || 1000;
    const groupName = req.query.group || null;
    const page = parseInt(req.query.page) || 1;
    const pageSize = parseInt(req.query.pageSize) || 20;

    console.log(`[Watchlist] 获取自选股: minCap=${minMarketCap}亿, group=${groupName || '全部'}, page=${page}`);

    // 调用 Python 富途服务获取数据
    const futuData = await getFutuData('watchlist', {
      minCap: minMarketCap,
      group: groupName,
      page: page,
      pageSize: pageSize
    });

    if (futuData.success && futuData.data) {
      console.log(`[Watchlist] 从 Futu 获取 ${futuData.data.length} 只自选股`);
      res.json({
        success: true,
        data: futuData.data,
        groups: futuData.groups || [],
        page: futuData.page || page,
        pageSize: futuData.pageSize || pageSize,
        total: futuData.total || futuData.data.length,
        source: 'futu',
        connected: futuData.connected,
        updateTime: Date.now()
      });
    } else {
      console.log(`[Watchlist] Futu 数据为空: ${futuData.error}`);
      res.json({
        success: false,
        error: futuData.error || '获取失败',
        data: [],
        groups: [],
        updateTime: Date.now()
      });
    }

  } catch (error) {
    console.error('[API] 获取自选股失败:', error);
    res.json({
      success: false,
      error: error.message,
      data: [],
      groups: [],
      updateTime: Date.now()
    });
  }
});

// 路由：手动添加股票到自选（临时显示）
app.post('/api/watchlist/add', async (req, res) => {
  try {
    const { codes } = req.body;
    
    if (!codes || !Array.isArray(codes) || codes.length === 0) {
      res.json({
        success: false,
        error: '请提供股票代码列表'
      });
      return;
    }

    console.log(`[Watchlist] 手动添加股票: ${codes.join(', ')}`);

    // 调用 Python 富途服务获取指定股票数据
    const futuData = await getFutuData('watchlist-custom', {
      codes: codes
    });

    if (futuData.success && futuData.data) {
      res.json({
        success: true,
        data: futuData.data,
        updateTime: Date.now()
      });
    } else {
      res.json({
        success: false,
        error: futuData.error || '获取失败',
        data: []
      });
    }

  } catch (error) {
    console.error('[API] 添加自选股失败:', error);
    res.json({
      success: false,
      error: error.message,
      data: []
    });
  }
});

// 生成模拟热门股票数据
function generateMockHotStocks() {
  const mockStocks = [
    { symbol: 'NVDA', name: 'NVIDIA', price: 875.50, change: 4.25, periodChange: 28.5, marketCap: 2150, changeText: '+28.50%' },
    { symbol: 'META', name: 'Meta Platforms', price: 485.20, change: 2.15, periodChange: 22.8, marketCap: 1230, changeText: '+22.80%' },
    { symbol: 'AMZN', name: 'Amazon', price: 178.35, change: 1.85, periodChange: 18.5, marketCap: 1850, changeText: '+18.50%' },
    { symbol: 'MSFT', name: 'Microsoft', price: 415.80, change: 1.25, periodChange: 15.2, marketCap: 3090, changeText: '+15.20%' },
    { symbol: 'GOOGL', name: 'Alphabet', price: 152.75, change: 0.95, periodChange: 12.8, marketCap: 1910, changeText: '+12.80%' },
    { symbol: 'TSLA', name: 'Tesla', price: 245.60, change: -0.85, periodChange: 11.5, marketCap: 780, changeText: '+11.50%' },
    { symbol: 'AAPL', name: 'Apple', price: 189.45, change: 0.55, periodChange: 8.5, marketCap: 2950, changeText: '+8.50%' },
    { symbol: 'AVGO', name: 'Broadcom', price: 1420.30, change: 2.45, periodChange: 18.2, marketCap: 660, changeText: '+18.20%' },
    { symbol: 'CRM', name: 'Salesforce', price: 285.90, change: 1.75, periodChange: 15.8, marketCap: 275, changeText: '+15.80%' },
    { symbol: 'AMD', name: 'AMD', price: 165.25, change: 3.25, periodChange: 25.5, marketCap: 267, changeText: '+25.50%' }
  ];
  return mockStocks;
}

// 启动服务器
const PORT = 3000;

console.log('=================================');
console.log('   Stock API Server Starting...');
console.log('=================================');
console.log(`   OpenD: ${FUTU_OPEND_HOST}:${FUTU_OPEND_PORT}`);
console.log(`   Python: ${PYTHON_SCRIPT}`);
console.log('=================================');

app.listen(PORT, () => {
  console.log('');
  console.log('=================================');
  console.log(`   Server running on port ${PORT}`);
  console.log('=================================');
  console.log('');
  console.log('API Endpoints:');
  console.log(`  GET http://localhost:${PORT}/api/hot-sectors`);
  console.log(`  GET http://localhost:${PORT}/api/hot-stocks`);
  console.log(`  GET http://localhost:${PORT}/api/watchlist`);
  console.log(`  GET http://localhost:${PORT}/api/trade-history`);
  console.log(`  GET http://localhost:${PORT}/api/health`);
  console.log(`  GET http://localhost:${PORT}/api/check-port`);
  console.log(` POST http://localhost:${PORT}/api/server/start`);
  console.log(` POST http://localhost:${PORT}/api/server/restart`);
  console.log('');
  console.log('交易记录参数:');
  console.log('  period: today | 1w | 1m');
  console.log('  market: HK | US');
  console.log('');
});
