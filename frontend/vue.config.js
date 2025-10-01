const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  transpileDependencies: true,
  
  // 开发服务器配置
  devServer: {
    // 启用压缩
    compress: true,
    // 启用热重载
    hot: true,
    // 减少日志输出
    client: {
      logging: 'warn'
    }
  },
  
  // 构建优化
  configureWebpack: config => {
    // 开发模式下的性能优化
    if (process.env.NODE_ENV === 'development') {
      // 启用文件系统缓存
      config.cache = {
        type: 'filesystem',
        buildDependencies: {
          config: [__filename]
        }
      }
      
      // 优化解析
      if (!config.resolve) config.resolve = {}
      config.resolve.symlinks = false
      if (!config.resolve.alias) config.resolve.alias = {}
      config.resolve.alias['@'] = require('path').resolve(__dirname, 'src')
    }
    
    // 代码分割优化
    if (!config.optimization) config.optimization = {}
    config.optimization.splitChunks = {
      chunks: 'all',
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all',
          priority: 10
        },
        elementPlus: {
          test: /[\\/]node_modules[\\/]element-plus[\\/]/,
          name: 'element-plus',
          chunks: 'all',
          priority: 20
        }
      }
    }
  },
  
  // 减少构建时间
  chainWebpack: config => {
    // 开发模式下禁用某些优化以提高构建速度
    if (process.env.NODE_ENV === 'development') {
      config.optimization.minimize(false)
      
      // 禁用source map以提高构建速度
      config.devtool('eval-cheap-module-source-map')
    }
  },
  
  // 并行处理
  parallel: require('os').cpus().length > 1,
  
  // 生产环境source map
  productionSourceMap: false
})