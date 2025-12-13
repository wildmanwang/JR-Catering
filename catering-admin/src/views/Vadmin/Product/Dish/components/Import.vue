/**
 * 菜品批量导入/维护页面
 * 
 * 功能特性：
 * 1. 从父窗口（Dish.vue）接收选中的菜品数据，支持批量编辑
 * 2. Excel 风格的表格交互（单元格编辑、键盘导航、复制粘贴）
 * 3. 支持新增、编辑、保存操作
 * 4. 自动加载菜品状态和厨部选项数据
 * 
 * 数据流程：
 * 父窗口（Dish.vue） -> sessionStorage -> ImportGrid 组件 -> 保存到后端
 * 
 * 使用方式：
 * 1. 在菜品列表页选择记录，点击"导入"按钮打开批量编辑页面
 * 2. 或直接访问 /product/dish/import 打开空白编辑页面
 * 
 * 技术说明：
 * - 使用 ImportGrid 通用组件实现 Excel 风格的表格编辑
 * - 通过 sessionStorage 在页面间传递数据
 * - 编辑模式下通过透明背景确保不遮挡单元格边框
 */
<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ContentWrap } from '@/components/ContentWrap'
import { ButtonPlus } from '@/components/ButtonPlus'
import { PrompInfo } from '@/components/PrompInfo'
import ImportGrid, { type ImportGridColumn } from '@/wintemplate/importGrid/ImportGrid.vue'
import { getDishStatusOptionsApi, addDishListApi, putDishListApi, getDishApi } from '@/api/vadmin/product/dish'
import { getKitchenListApi } from '@/api/vadmin/product/kitchen'
import { useAuthStore } from '@/store/modules/auth'

defineOptions({
  name: 'DishImport'
})

// ==================== 常量定义 ====================

/** 导入数据存储的 sessionStorage key（与父窗口 Dish.vue 保持一致） */
const IMPORT_STORAGE_KEY = 'IMPORT_DISH_PAYLOAD'

// ==================== 数据配置 ====================

/**
 * 创建默认行数据
 * 
 * 用于新增行时提供默认值，确保所有字段都有初始值
 * 
 * @returns {object} 默认行数据对象
 */
const createDefaultRow = () => ({
  id: undefined,
  name_unique: '',
  name_display: undefined,
  name_english: undefined,
  kitchen_id: undefined,
  spec: undefined,
  price: undefined,
  order_number: undefined,
  status: -1,
  dish_images: [],
  dish_images_display: []
})

/**
 * 列配置
 * 
 * 定义表格显示的列及其属性（宽度、类型、是否可编辑等）
 * 使用 computed 确保选项数据更新时列配置也会更新
 */
const columns = computed<ImportGridColumn[]>(() => [
  {
    field: 'id',
    label: 'ID',
    width: '80px',
    type: 'text',
    show: false
  },
  {
    field: 'name_unique',
    label: '名称',
    minWidth: '200px',
    type: 'text',
    show: true,
    required: true
  },
  {
    field: 'name_display',
    label: '显示名称',
    minWidth: '200px',
    type: 'text',
    show: true,
    required: true
  },
  {
    field: 'name_english',
    label: '英文名称',
    minWidth: '200px',
    type: 'text',
    show: true
  },
  {
    field: 'kitchen_id',
    label: '厨部',
    width: '100px',
    type: 'select',
    show: true,
    required: true,
    options: kitchenOptions.value,
    selectProps: {
      disabled: false,
      filterable: false
    }
  },
  {
    field: 'spec',
    label: '规格',
    width: '160px',
    type: 'text',
    show: true
  },
  {
    field: 'price',
    label: '基础售价',
    width: '120px',
    type: 'number',
    show: true
  },
  {
    field: 'order_number',
    label: '排序号',
    width: '80px',
    type: 'number',
    show: true
  },
  {
    field: 'dish_images',
    label: '图片',
    width: '480px',
    type: 'image',
    show: true
  },
  {
    field: 'status',
    label: '状态',
    width: '60px',
    type: 'select',
    show: true,
    options: dishStatusOptions.value,
    selectProps: {
      disabled: true,
      filterable: false
    }
  }
])

/**
 * 数据转换函数
 * 
 * 将父窗口（Dish.vue）传入的数据转换为表格所需格式
 * 确保所有字段都有默认值，避免显示异常
 * 
 * @param {any} row - 父窗口传入的行数据
 * @returns {object} 转换后的行数据
 */
const mapRowData = (row: any) => {
  return {
    ...row,
    // 确保所有字段都有默认值
    name_unique: row.name_unique ?? '',
    name_display: row.name_display ?? row.name_unique ?? '',
    name_english: row.name_english ?? null,
    kitchen_id: row.kitchen_id ?? 1,
    price: row.price ?? null,
    order_number: row.order_number ?? null,
    spec: row.spec ?? null,
    unit: row.unit ?? null,
    status: row.status ?? -1,
    dish_images: Array.isArray(row.dish_images) ? row.dish_images : [],
    dish_images_display: Array.isArray(row.dish_images_display) ? row.dish_images_display : []
  }
}

// ==================== 组件引用 ====================

/** ImportGrid 组件引用（用于调用组件方法） */
const importGridRef = ref<InstanceType<typeof ImportGrid>>()

/** PrompInfo 组件引用（用于显示提示信息） */
const prompInfoRef = ref<InstanceType<typeof PrompInfo>>()

// ==================== 状态管理 ====================

/** 保存操作的加载状态 */
const saveLoading = ref(false)

/** 菜品状态选项 */
const dishStatusOptions = ref<Array<{ label: string; value: number }>>([])

/** 厨部选项 */
const kitchenOptions = ref<Array<{ label: string; value: number }>>([])

/** 原始数据（用于判断是否修改） */
const originalData = ref<any[]>([])

/** Auth Store（用于获取上传 token） */
const authStore = useAuthStore()
const token = computed(() => authStore.getToken)

// ==================== 事件处理 ====================

/**
 * 数据加载完成回调
 * 
 * ImportGrid 组件从 sessionStorage 加载数据后触发
 * 
 * @param _data - 加载的数据列表
 */
const handleDataLoaded = (_data: any[]) => {
  // 保存原始数据，用于判断是否修改
  originalData.value = JSON.parse(JSON.stringify(_data || []))
  prompInfoRef.value?.ready()
}

/**
 * 数据变化回调
 * 
 * 表格数据发生变化时触发（新增、删除、编辑单元格）
 * 
 * @param _data - 当前的数据列表（当前未使用）
 */
const handleDataChanged = (_data: any[]) => {
  // 数据变化时的处理逻辑（如需要）
}

/**
 * 上传图片文件
 */
const uploadFile = async (file: FormData) => {
  try {
    const res = await fetch('/api/vadmin/system/upload/image/to/local', {
      method: 'POST',
      body: file,
      headers: {
        'Authorization': token.value || ''
      }
    })

    if (!res.ok) {
      throw new Error(`HTTP错误！状态：${res.status}`)
    }

    const data = await res.json()
    return {
      success: true,
      message: '上传成功',
      data: data
    }
  } catch (err) {
    const msg = err instanceof Error ? err.message : '未知的错误.'
    return {
      success: false,
      message: msg
    }
  }
}

/**
 * 处理图片字段，将图片数组转换为提交格式
 * 参考 BaseFree 的 handleImageUpload 函数
 * 
 * ImportGrid 中图片格式：
 * - 新上传的图片： [previewUrl, 'add', file.name, file] 其中 file.raw 是文件对象
 * - 已存在的图片：字符串格式，如 "path/to/image?original" 或 "path/to/image?delete"
 */
const processImageField = async (row: any) => {
  const imageField = 'dish_images'
  const imageDisplayField = 'dish_images_display'
  
  // 检查字段是否存在且为数组
  if (!row[imageField] || !Array.isArray(row[imageField])) {
    return
  }
  
  // 处理每个图片项
  for (let index = 0; index < row[imageField].length; index++) {
    const fileData = row[imageField][index]
    
    // 如果是数组格式（包含文件对象），说明是未上传的图片，需要上传
    if (Array.isArray(fileData)) {
      const fileForm = new FormData()
      fileForm.append('file', fileData[3].raw)
      fileForm.append('path', 'system')
      const res = await uploadFile(fileForm)
      if (!res.success) {
        throw new Error(`图片上传错误：${res.message}`)
      }
      // 转换为字符串格式：路径 + 操作类型（add/update/delete）
      row[imageField][index] = `${res.data.data.remote_path}?${fileData[1]}`
      row[imageDisplayField][index] = `${res.data.data.remote_path}?${fileData[1]}`
    }
    // 如果已经是字符串格式，保持不变
    // 如果包含 ?delete 标记，保持原样（用于删除操作）
  }
}

/**
 * 判断数据是否被修改
 */
const isDataModified = (currentRow: any, originalRow: any): boolean => {
  if (!originalRow) return true // 新增记录
  
  // 比较关键字段
  const fieldsToCompare = [
    'name_unique', 'name_display', 'name_english', 'kitchen_id',
    'spec', 'price', 'order_number', 'dish_images'
  ]
  
  for (const field of fieldsToCompare) {
    if (field === 'dish_images') {
      // 图片字段需要特殊比较
      const currentImages = JSON.stringify((currentRow[field] || []).sort())
      const originalImages = JSON.stringify((originalRow[field] || []).sort())
      if (currentImages !== originalImages) {
        return true
      }
    } else {
      if (currentRow[field] !== originalRow[field]) {
        return true
      }
    }
  }
  
  return false
}

// ==================== 数据获取 ====================

/**
 * 获取菜品状态选项
 */
const getDishStatusOptions = async () => {
  try {
    const res = await getDishStatusOptionsApi()
    dishStatusOptions.value = res?.data || []
  } catch (err) {
    console.error('获取菜品状态列表失败：', err)
    dishStatusOptions.value = []
  }
}

/**
 * 获取厨部列表选项
 */
const getKitchenOptions = async () => {
  try {
    const res = await getKitchenListApi({ is_active: true })
    if (!res?.data) {
      kitchenOptions.value = []
      return
    }
    // 转换为下拉选项格式：{ label: string, value: number }
    kitchenOptions.value = res.data.map((kitchen: any) => ({
      label: kitchen.name_unique || `厨部${kitchen.id}`,
      value: kitchen.id
    }))
  } catch (err) {
    console.error('获取厨部列表失败：', err)
    kitchenOptions.value = []
  }
}

// ==================== 操作方法 ====================

/**
 * 新增行
 * 
 * 在表格末尾添加一行默认数据
 */
const handleAddRow = () => {
  const data = importGridRef.value?.getData() || []
  const newRow = createDefaultRow()
  data.push(newRow)
  importGridRef.value?.setData(data)
  prompInfoRef.value?.info('已新增 1 行')
}

/**
 * 保存数据
 * 
 * 将表格中的所有数据保存到后端
 * 逐行处理，支持新增和修改
 */
const handleSave = async () => {
  const data = importGridRef.value?.getData() || []
  if (!data.length) {
    prompInfoRef.value?.warn('没有数据需要保存。')
    return
  }
  
  // 数据校验：检查必填字段
  const requiredFields = [
    { field: 'name_unique', label: '名称' },
    { field: 'name_display', label: '显示名称' },
    { field: 'kitchen_id', label: '厨部' }
  ]
  
  const errors: string[] = []
  data.forEach((row: any, index: number) => {
    requiredFields.forEach(({ field, label }) => {
      const value = row[field]
      if (value === undefined || value === null || value === '') {
        errors.push(`第 ${index + 1} 行：${label} 为必填项`)
      }
    })
  })
  
  if (errors.length > 0) {
    prompInfoRef.value?.err(errors.join('；'))
    return
  }
  
  // 筛选需要保存的数据
  const dataToSave: Array<{ row: any; index: number; isNew: boolean; originalRow: any }> = []
  
  for (let i = 0; i < data.length; i++) {
    const row = data[i]
    const originalRow = originalData.value[i]
    const isNew = !row.id || row.id === undefined || row.id === null || row.id === ''
    
    if (isNew) {
      // 新增记录，直接添加
      dataToSave.push({ row, index: i, isNew: true, originalRow: null })
    } else {
      // 修改记录，需要判断是否被修改
      if (isDataModified(row, originalRow)) {
        dataToSave.push({ row, index: i, isNew: false, originalRow })
      }
    }
  }
  
  if (dataToSave.length === 0) {
    prompInfoRef.value?.warn('没有数据需要保存。')
    return
  }
  
  saveLoading.value = true
  
  let addCount = 0
  let updateCount = 0
  
  try {
    // 逐行处理
    for (const { row, index, isNew } of dataToSave) {
      // 设置当前行
      importGridRef.value?.setCurrentRow(index)
      
      // 显示进度
      if (isNew) {
        prompInfoRef.value?.info(`正在提交第 ${index + 1} 行...`)
      } else {
        prompInfoRef.value?.info(`正在提交第 ${index + 1} 行...`)
      }
      
      try {
        // 先处理图片字段（上传新图片并转换为字符串格式）
        // 注意：直接修改 row，因为我们需要保留文件对象用于上传
        await processImageField(row)
        
        // 处理完图片后，深拷贝行数据（此时所有图片都已经是字符串格式）
        const submitData = JSON.parse(JSON.stringify(row))
        
        // 确保 dish_images 是字符串数组，移除任何非字符串项
        if (Array.isArray(submitData.dish_images)) {
          submitData.dish_images = submitData.dish_images.filter((item: any) => typeof item === 'string')
        }
        
        // 移除 dish_images_display 字段，后端不需要这个字段
        delete submitData.dish_images_display
        
        // 新增记录：status 替换为 0（提交时，表格中不变）
        // 注意：只修改 submitData，不修改 row，保持表格中的值不变
        if (isNew) {
          submitData.status = 0
        }
        
        // 提交数据
        let res
        if (isNew) {
          res = await addDishListApi(submitData)
        } else {
          res = await putDishListApi(submitData)
        }
        
        if (res.code !== 200) {
          throw new Error(res.msg || '保存失败')
        }
        
        // 保存成功后，从数据库重新获取该条记录（获取 id）
        if (isNew) {
          // 新增记录，从返回结果获取 id
          const newId = res.data?.id || (res.data && typeof res.data === 'object' && 'id' in res.data ? res.data.id : null)
          if (newId) {
            // 重新获取完整记录
            const detailRes = await getDishApi(newId)
            if (detailRes.code === 200 && detailRes.data) {
              // 更新表格中的数据，但保持其他行不变
              const currentData = importGridRef.value?.getData() || []
              const detail = detailRes.data
              
              // 处理图片数据格式（参考 Dish.vue 的数据处理逻辑）
              if (detail.dish_images) {
                detail.dish_images.sort((a: string, b: string) => a.localeCompare(b))
                detail.dish_images = detail.dish_images.map((p: string) => p.split('-').slice(1).join('-'))
              }
              
              // 转换为导入格式
              const normalizedImages = Array.isArray(detail.dish_images) 
                ? detail.dish_images.filter((img: any) => typeof img === 'string' && img) 
                : []
              const normalizeImage = (img: string) => {
                if (typeof img !== 'string' || !img.length) return ''
                const [path] = img.split('?')
                return path ? `${path}?original` : ''
              }
              
              currentData[index] = {
                ...currentData[index],
                id: detail.id,
                name_unique: detail.name_unique ?? currentData[index].name_unique,
                name_display: detail.name_display ?? currentData[index].name_display,
                name_english: detail.name_english ?? currentData[index].name_english,
                kitchen_id: detail.kitchen_id ?? currentData[index].kitchen_id,
                price: detail.price ?? currentData[index].price,
                order_number: detail.order_number ?? currentData[index].order_number,
                spec: detail.spec ?? currentData[index].spec,
                status: detail.status ?? currentData[index].status,
                dish_images: normalizedImages.map(normalizeImage).filter(Boolean),
                dish_images_display: [...normalizedImages]
              }
              
              importGridRef.value?.setData(currentData)
              
              // 更新原始数据
              originalData.value[index] = JSON.parse(JSON.stringify(currentData[index]))
            }
          }
          addCount++
        } else {
          // 修改记录，重新获取完整记录
          const detailRes = await getDishApi(row.id)
          if (detailRes.code === 200 && detailRes.data) {
            const currentData = importGridRef.value?.getData() || []
            const detail = detailRes.data
            
            // 处理图片数据格式
            if (detail.dish_images) {
              detail.dish_images.sort((a: string, b: string) => a.localeCompare(b))
              detail.dish_images = detail.dish_images.map((p: string) => p.split('-').slice(1).join('-'))
            }
            
            // 转换为导入格式
            const normalizedImages = Array.isArray(detail.dish_images) 
              ? detail.dish_images.filter((img: any) => typeof img === 'string' && img) 
              : []
            const normalizeImage = (img: string) => {
              if (typeof img !== 'string' || !img.length) return ''
              const [path] = img.split('?')
              return path ? `${path}?original` : ''
            }
            
            currentData[index] = {
              ...currentData[index],
              name_unique: detail.name_unique ?? currentData[index].name_unique,
              name_display: detail.name_display ?? currentData[index].name_display,
              name_english: detail.name_english ?? currentData[index].name_english,
              kitchen_id: detail.kitchen_id ?? currentData[index].kitchen_id,
              price: detail.price ?? currentData[index].price,
              order_number: detail.order_number ?? currentData[index].order_number,
              spec: detail.spec ?? currentData[index].spec,
              status: detail.status ?? currentData[index].status,
              dish_images: normalizedImages.map(normalizeImage).filter(Boolean),
              dish_images_display: [...normalizedImages]
            }
            
            importGridRef.value?.setData(currentData)
            
            // 更新原始数据
            originalData.value[index] = JSON.parse(JSON.stringify(currentData[index]))
          }
          updateCount++
        }
      } catch (err: any) {
        const errorMsg = err.message || err.msg || '保存失败'
        prompInfoRef.value?.err(`第 ${index + 1} 行：${errorMsg}，修改后点击"保存"继续处理...`)
        // 中断整个处理流程
        saveLoading.value = false
        return
      }
    }
    
    // 显示最终统计
    const messages: string[] = []
    if (addCount > 0) {
      messages.push(`新增了 ${addCount} 条`)
    }
    if (updateCount > 0) {
      messages.push(`修改了 ${updateCount} 条`)
    }
    if (messages.length > 0) {
      prompInfoRef.value?.info(`成功${messages.join('、')}数据。`)
    }
    
    // 清除当前行
    importGridRef.value?.setCurrentRow(null)
  } catch (err) {
    console.error('保存失败：', err)
    prompInfoRef.value?.err('保存失败，请稍后重试')
  } finally {
    saveLoading.value = false
  }
}

onMounted(async () => {
  // 获取选项数据
  await Promise.all([
    getDishStatusOptions(),
    getKitchenOptions()
  ])
  
  // 组件挂载后，ImportGrid 会自动从 sessionStorage 加载数据
  prompInfoRef.value?.ready()
})
</script>

<template>
  <ContentWrap>
    <!-- 工具栏 -->
    <div class="import-toolbar">
      <div class="toolbar-left">
        <ButtonPlus stype="new" @click="handleAddRow" />
      </div>
      <div class="toolbar-info">
        <PrompInfo ref="prompInfoRef" />
      </div>
      <div class="toolbar-right">
        <ButtonPlus stype="save" :loading="saveLoading" @click="handleSave" />
      </div>
    </div>
    
    <!-- 表格 -->
    <ImportGrid
      ref="importGridRef"
      :columns="columns"
      :storage-key="IMPORT_STORAGE_KEY"
      :create-default-row="createDefaultRow"
      :map-row-data="mapRowData"
      @data-loaded="handleDataLoaded"
      @data-changed="handleDataChanged"
    />
  </ContentWrap>
</template>

<style lang="less" scoped>
/* 确保 ContentWrap 内部的布局正确，移除所有 padding */
:deep(.content-wrap) {
  height: 100% !important;
  display: flex !important;
  flex-direction: column !important;
  padding: 0 !important;
}

:deep(.content-wrap .el-card) {
  height: 100% !important;
  display: flex !important;
  flex-direction: column !important;
  padding: 0 !important;
}

:deep(.content-wrap .el-card__body) {
  flex: 1 !important;
  display: flex !important;
  flex-direction: column !important;
  min-height: 0 !important;
  overflow: hidden !important;
  padding: 0 !important;
}

:deep(.content-wrap > div) {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  height: 100%;
}

/* 工具栏 */
.import-toolbar {
  display: flex;
  align-items: center;
  margin: 0;
  gap: 10px;
}

.toolbar-left {
  flex: 0 0 auto;
}

.toolbar-info {
  flex: 1;
  min-width: 0; // 允许收缩
}

.toolbar-right {
  flex: 0 0 auto;
}

/* 移除 ImportGrid 容器的 padding */
:deep(.import-grid-container) {
  padding: 0 !important;
}
</style>

<style lang="less">
/* 
 * 全局样式：编辑模式下隐藏 wrapper 的边框和背景
 * 
 * 说明：通过设置透明背景确保不遮挡单元格的边框，提供更好的视觉效果
 * 适用于所有 Element Plus 输入组件（Input、Select、InputNumber）
 */
.import-grid-container .el-table__cell.editing-cell {
  /* 所有 wrapper 元素和内部元素 */
  .el-input__wrapper,
  .el-select__wrapper,
  .el-input-number__input-wrapper,
  .el-input-number .el-input__wrapper,
  .el-input__inner,
  input,
  textarea {
    border: none !important;
    border-width: 0 !important;
    border-color: transparent !important;
    background: transparent !important;
    background-color: transparent !important;
    box-shadow: none !important;
    outline: none !important;
  }
  
  /* 所有状态（hover、focus 等） */
  .el-input__wrapper:hover,
  .el-input__wrapper:focus,
  .el-input__wrapper:focus-within,
  .el-input__wrapper.is-focus,
  .el-input__wrapper.is-hover,
  .el-select__wrapper:hover,
  .el-select__wrapper:focus,
  .el-select__wrapper:focus-within,
  .el-select__wrapper.is-focus,
  .el-select__wrapper.is-hover,
  .el-input-number__input-wrapper:hover,
  .el-input-number__input-wrapper:focus,
  .el-input-number__input-wrapper:focus-within,
  .el-input-number__input-wrapper.is-focus,
  .el-input-number__input-wrapper.is-hover,
  .el-input-number .el-input__wrapper:hover,
  .el-input-number .el-input__wrapper:focus,
  .el-input-number .el-input__wrapper:focus-within,
  .el-input-number .el-input__wrapper.is-focus,
  .el-input-number .el-input__wrapper.is-hover,
  .el-input__inner:hover,
  .el-input__inner:focus,
  input:hover,
  input:focus,
  textarea:hover,
  textarea:focus {
    border: none !important;
    border-width: 0 !important;
    border-color: transparent !important;
    background: transparent !important;
    background-color: transparent !important;
    box-shadow: none !important;
    outline: none !important;
  }
}
</style>

