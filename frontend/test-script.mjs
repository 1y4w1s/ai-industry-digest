/**
 * AI 行业资讯聚合平台 - 前端测试脚本
 * 运行方式: node test-script.mjs
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { execSync } from 'child_process';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

class TestRunner {
  constructor() {
    this.passed = 0;
    this.failed = 0;
    this.results = [];
  }

  async run() {
    console.log('\n========================================');
    console.log('  AI 行业资讯聚合平台 - 前端测试');
    console.log('========================================\n');

    await this.testEnvironment();
    await this.testBuild();
    await this.testConfig();
    await this.testAuth();

    this.summary();
  }

  async testEnvironment() {
    console.log('【测试模块】环境配置');
    console.log('------------------------');

    const tests = [
      {
        name: '检查 Node.js 版本',
        run: () => {
          const version = process.version;
          const major = parseInt(version.split('.')[0].replace('v', ''));
          return major >= 18 ? { pass: true, msg: `Node.js ${version} (支持)` } : { pass: false, msg: `Node.js ${version} (需要 >= 18)` };
        }
      },
      {
        name: '检查 npm 版本',
        run: () => {
          try {
            const version = execSync('npm --version').toString().trim();
            return { pass: true, msg: `npm ${version}` };
          } catch {
            return { pass: false, msg: 'npm 未安装' };
          }
        }
      },
      {
        name: '检查前端目录结构',
        run: () => {
          const dirs = ['src', 'public', 'dist', 'node_modules'];
          const missing = dirs.filter(d => !fs.existsSync(path.join(__dirname, d)));
          return missing.length === 0 
            ? { pass: true, msg: '目录结构完整' } 
            : { pass: false, msg: `缺少目录: ${missing.join(', ')}` };
        }
      }
    ];

    await this.runTests(tests);
  }

  async testBuild() {
    console.log('\n【测试模块】构建验证');
    console.log('------------------------');

    const tests = [
      {
        name: '检查 package.json 存在',
        run: () => {
          const exists = fs.existsSync(path.join(__dirname, 'package.json'));
          return { pass: exists, msg: exists ? '存在' : '不存在' };
        }
      },
      {
        name: '检查构建脚本配置',
        run: () => {
          const pkg = JSON.parse(fs.readFileSync(path.join(__dirname, 'package.json'), 'utf-8'));
          const hasBuild = pkg.scripts && pkg.scripts.build;
          return { pass: hasBuild, msg: hasBuild ? `build: ${pkg.scripts.build}` : '缺少 build 脚本' };
        }
      },
      {
        name: '检查构建产物',
        run: () => {
          const distPath = path.join(__dirname, 'dist');
          const hasIndex = fs.existsSync(path.join(distPath, 'index.html'));
          const hasAssets = fs.existsSync(path.join(distPath, 'assets'));
          return { pass: hasIndex && hasAssets, msg: hasIndex && hasAssets ? '构建产物完整' : '构建产物不完整' };
        }
      },
      {
        name: '检查构建产物大小',
        run: () => {
          const jsFiles = fs.readdirSync(path.join(__dirname, 'dist', 'assets')).filter(f => f.endsWith('.js'));
          if (jsFiles.length === 0) return { pass: false, msg: '无 JS 文件' };
          const sizes = jsFiles.map(f => {
            const size = fs.statSync(path.join(__dirname, 'dist', 'assets', f)).size / 1024;
            return `${f}: ${size.toFixed(1)} KB`;
          });
          return { pass: true, msg: sizes.join(', ') };
        }
      }
    ];

    await this.runTests(tests);
  }

  async testConfig() {
    console.log('\n【测试模块】配置验证');
    console.log('------------------------');

    const tests = [
      {
        name: '检查 .env 文件',
        run: () => {
          const exists = fs.existsSync(path.join(__dirname, '.env'));
          return { pass: exists, msg: exists ? '存在' : '不存在' };
        }
      },
      {
        name: '检查 Supabase URL 配置',
        run: () => {
          const env = fs.readFileSync(path.join(__dirname, '.env'), 'utf-8');
          const hasUrl = env.includes('VITE_SUPABASE_URL=');
          const isValid = env.includes('https://') && env.includes('.supabase.co');
          return { pass: hasUrl && isValid, msg: hasUrl ? (isValid ? '配置有效' : '配置无效') : '缺少配置' };
        }
      },
      {
        name: '检查 Supabase Key 配置',
        run: () => {
          const env = fs.readFileSync(path.join(__dirname, '.env'), 'utf-8');
          const hasKey = env.includes('VITE_SUPABASE_ANON_KEY=');
          const isValid = hasKey && env.match(/VITE_SUPABASE_ANON_KEY=\S{50,}/);
          return { pass: hasKey && isValid, msg: hasKey ? (isValid ? '配置有效' : '密钥格式无效') : '缺少配置' };
        }
      },
      {
        name: '检查 API 配置',
        run: () => {
          const env = fs.readFileSync(path.join(__dirname, '.env'), 'utf-8');
          const hasApi = env.includes('VITE_API_URL=');
          return { pass: hasApi, msg: hasApi ? `API_URL: ${env.match(/VITE_API_URL=(\S+)/)[1]}` : '缺少配置' };
        }
      },
      {
        name: '检查 vite.config.js',
        run: () => {
          const exists = fs.existsSync(path.join(__dirname, 'vite.config.js'));
          return { pass: exists, msg: exists ? '存在' : '不存在' };
        }
      }
    ];

    await this.runTests(tests);
  }

  async testAuth() {
    console.log('\n【测试模块】认证功能');
    console.log('------------------------');

    const tests = [
      {
        name: '检查 AuthContext 组件',
        run: () => {
          const exists = fs.existsSync(path.join(__dirname, 'src', 'context', 'AuthContext.jsx'));
          return { pass: exists, msg: exists ? '存在' : '不存在' };
        }
      },
      {
        name: '检查登录页面',
        run: () => {
          const exists = fs.existsSync(path.join(__dirname, 'src', 'pages', 'LoginPage.jsx'));
          return { pass: exists, msg: exists ? '存在' : '不存在' };
        }
      },
      {
        name: '检查 supabase 配置',
        run: () => {
          const ctx = fs.readFileSync(path.join(__dirname, 'src', 'context', 'AuthContext.jsx'), 'utf-8');
          const hasGetSession = ctx.includes('getSession');
          const hasOldSession = ctx.includes('supabase.auth.session(');
          return { pass: hasGetSession && !hasOldSession, msg: hasGetSession ? '使用 getSession() (SDK v2)' : '可能使用了废弃的 session()' };
        }
      },
      {
        name: '检查 useAuth hook',
        run: () => {
          const ctx = fs.readFileSync(path.join(__dirname, 'src', 'context', 'AuthContext.jsx'), 'utf-8');
          const hasHook = ctx.includes('useAuth') && ctx.includes('createContext');
          return { pass: hasHook, msg: hasHook ? 'useAuth hook 配置正确' : '配置不完整' };
        }
      }
    ];

    await this.runTests(tests);
  }

  async runTests(tests) {
    for (const test of tests) {
      try {
        const result = test.run();
        if (result.pass) {
          console.log(`✓ ${test.name}: ${result.msg}`);
          this.passed++;
        } else {
          console.log(`✗ ${test.name}: ${result.msg}`);
          this.failed++;
        }
        this.results.push({ name: test.name, pass: result.pass, msg: result.msg });
      } catch (error) {
        console.log(`✗ ${test.name}: 测试异常 - ${error.message}`);
        this.failed++;
        this.results.push({ name: test.name, pass: false, msg: `测试异常: ${error.message}` });
      }
    }
  }

  summary() {
    console.log('\n========================================');
    console.log('              测试结果汇总');
    console.log('========================================');
    console.log(`通过: ${this.passed} 项`);
    console.log(`失败: ${this.failed} 项`);
    console.log(`成功率: ${((this.passed / (this.passed + this.failed)) * 100).toFixed(1)}%`);
    
    if (this.failed > 0) {
      console.log('\n失败项详情:');
      this.results.filter(r => !r.pass).forEach((r, i) => {
        console.log(`${i + 1}. ${r.name}: ${r.msg}`);
      });
      process.exit(1);
    }
    
    console.log('\n✓ 所有测试通过！');
    process.exit(0);
  }
}

// 运行测试
const runner = new TestRunner();
runner.run();
