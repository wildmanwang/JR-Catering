<script setup lang="tsx">
import { computed, ref, toRefs, watch } from 'vue'
import { ElUpload, UploadProps, ElIcon, ElImage, ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { useAuthStore } from '@/store/modules/auth'

defineOptions({
  name: 'ImagePlus'
})

// ==================== Props 定义 ====================
interface Props {
  /** 图片数据数组（用于存储和提交） */
  modelValue?: any[]
  /** 是否禁用（查看模式） */
  disabled?: boolean
  /** 最大上传数量 */
  limit?: number
  /** 上传接口地址 */
  action?: string
  /** 上传时的额外数据 */
  data?: Record<string, any>
  /** 上传时的请求头 */
  headers?: Record<string, string>
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: () => [],
  disabled: false,
  limit: 10,
  action: '/api/vadmin/system/upload/image/to/local',
  data: () => ({ path: 'system' }),
  headers: () => ({})
})

// ==================== Emits 定义 ====================
const emit = defineEmits<{
  'update:modelValue': [value: any[]]
}>()

// ==================== Store ====================
const authStore = useAuthStore()
const token = computed(() => authStore.getToken)

// ==================== 计算属性 ====================
/** 当前图片数据 */
const imageData = computed({
  get: () => props.modelValue || [],
  set: (val) => emit('update:modelValue', val)
})

// 解构 props 以便在模板中直接使用（使用 toRefs 保持响应性）
const { disabled, action, data, limit } = toRefs(props)

// ==================== 内部显示数据（自动维护）====================
/** 显示用的图片数组（组件内部自动维护） */
const imageDisplayData = ref<any[]>([])

/**
 * 根据 modelValue 生成 displayValue
 * 处理逻辑：
 * 1. 如果是数组格式（新上传的图片），使用预览 URL
 * 2. 如果是字符串格式，移除操作标记（?original、?add 等），只保留路径用于显示
 * 3. 标记为 ?delete 的图片不显示（已删除）
 */
const generateDisplayData = (imageData: any[]): any[] => {
  if (!imageData || !Array.isArray(imageData)) {
    return []
  }

  return imageData
    .filter((item: any) => {
      // 过滤掉标记为删除的图片
      if (typeof item === 'string' && item.includes('?delete')) {
        return false
      }
      return true
    })
    .map((item: any) => {
      // 如果是数组格式（新上传的图片），使用预览 URL（第一个元素）
      if (Array.isArray(item) && item.length > 0) {
        return item[0]
      }
      // 如果是字符串格式，移除操作标记，只保留路径
      if (typeof item === 'string') {
        // 移除操作标记（?original、?add 等），但保留 ?delete 标记用于过滤
        if (item.includes('?')) {
          return item.split('?')[0]
        }
        return item
      }
      return item
    })
}

/**
 * 初始化显示数据
 */
const initDisplayData = () => {
  imageDisplayData.value = generateDisplayData(imageData.value)
}

// 初始化显示数据
initDisplayData()

// 内部更新标志，用于区分是组件内部操作还是外部数据变化
const isInternalUpdate = ref(false)

// 监听 modelValue 变化，自动更新显示数据
watch(
  () => props.modelValue,
  (newValue) => {
    // 如果是组件内部操作导致的更新，跳过（因为内部操作已经更新了显示数据）
    if (isInternalUpdate.value) {
      isInternalUpdate.value = false
      return
    }

    // 外部数据变化，更新显示数据
    if (newValue && Array.isArray(newValue)) {
      imageDisplayData.value = generateDisplayData(newValue)
    } else {
      imageDisplayData.value = []
    }
  },
  { deep: true, immediate: false }
)

// ==================== 上传前验证 ====================
const beforeImageUpload: UploadProps['beforeUpload'] = (rawFile) => {
  const isImage = ['image/jpeg', 'image/gif', 'image/png'].includes(rawFile.type)
  const isLtSize = rawFile.size / 1024 / 1024 < 2
  if (!isImage) {
    ElMessage.error('上传图片必须是 JPG/GIF/PNG/ 格式!')
  }
  if (!isLtSize) {
    ElMessage.error('上传图片大小不能超过2MB!')
  }
  return isImage && isLtSize
}

// ==================== 文件变化处理 ====================
const handleFileChange: UploadProps['onChange'] = (file) => {
  if (file.raw) {
    const exists = imageData.value.some((item: any) => {
      if (Array.isArray(item)) {
        return item[2] === file.name
      }
      return false
    })
    if (!exists) {
      const previewUrl = URL.createObjectURL(file.raw)
      // 更新图片数据（添加新上传的图片）
      const newImageData = [...imageData.value, [previewUrl, 'add', file.name, file]]
      isInternalUpdate.value = true
      imageData.value = newImageData
      // 自动更新显示数据
      imageDisplayData.value = generateDisplayData(newImageData)
    }
  }
}

// ==================== 删除图片 ====================
const handleRemoveImage = (index: number) => {
  if (Array.isArray(imageData.value[index])) {
    // 如果是新上传的图片（数组格式），直接删除
    const newImageData = [...imageData.value]
    newImageData.splice(index, 1)
    isInternalUpdate.value = true
    imageData.value = newImageData
    // 自动更新显示数据
    imageDisplayData.value = generateDisplayData(newImageData)
  } else {
    // 如果是已存在的图片（字符串格式），标记为删除
    const newImageData = [...imageData.value]
    const currentItem = newImageData[index]
    if (typeof currentItem === 'string') {
      // 移除原有标记，添加删除标记
      const path = currentItem.split('?')[0]
      newImageData[index] = `${path}?delete`
      isInternalUpdate.value = true
      imageData.value = newImageData
      // 自动更新显示数据（删除标记的图片会被过滤掉，不显示）
      imageDisplayData.value = generateDisplayData(newImageData)
    }
  }
}

// ==================== 拖拽排序 ====================
const dragIndex = ref(-1)
const dragOverIndex = ref(-1)

const handleDragStart = (index: number, event: DragEvent) => {
  if (props.disabled) return
  dragIndex.value = index
  event.dataTransfer!.effectAllowed = 'move'
  event.dataTransfer!.setData('text/plain', index.toString())
  setTimeout(() => {
    ;(event.target as HTMLElement).classList.add('dragging')
  }, 0)
}

const handleDragOver = (event: DragEvent) => {
  if (props.disabled) return
  event.preventDefault()
  event.dataTransfer!.dropEffect = 'move'
}

const handleDragEnter = (index: number, event: DragEvent) => {
  if (props.disabled) return
  event.preventDefault()
  dragOverIndex.value = index
}

const handleDragLeave = (event: DragEvent) => {
  if (props.disabled) return
  if (!(event.currentTarget as HTMLElement).contains(event.relatedTarget as HTMLElement)) {
    dragOverIndex.value = -1
  }
}

const handleDrop = (targetIndex: number, event: DragEvent) => {
  if (props.disabled) return
  event.preventDefault()
  const sourceIndex = parseInt(event.dataTransfer!.getData('text/plain'))
  if (sourceIndex !== targetIndex && sourceIndex >= 0 && targetIndex >= 0) {
    // 更新图片数据
    const imagesData = [...imageData.value]
    const [movedItem] = imagesData.splice(sourceIndex, 1)
    imagesData.splice(targetIndex, 0, movedItem)
    isInternalUpdate.value = true
    imageData.value = imagesData
    // 自动更新显示数据
    imageDisplayData.value = generateDisplayData(imagesData)
  }
  dragIndex.value = -1
  dragOverIndex.value = -1
}

const handleDragEnd = () => {
  if (props.disabled) return
  dragIndex.value = -1
  dragOverIndex.value = -1
  const draggingElements = document.querySelectorAll('.dragging')
  draggingElements.forEach((el) => {
    el.classList.remove('dragging')
  })
}

// ==================== 生成预览列表 ====================
/**
 * 生成预览列表：过滤掉删除标记和 OSS 参数
 */
const generatePreviewList = (): string[] => {
  if (!imageDisplayData.value || !Array.isArray(imageDisplayData.value)) {
    return []
  }
  return imageDisplayData.value
    .filter((img: string) => img && !img.endsWith('?delete'))
    .map((img: string) => {
      // 移除 OSS 参数，使用原始图片进行预览
      if (typeof img === 'string' && img.includes('?')) {
        const [path] = img.split('?')
        return path || img
      }
      return img
    })
    .filter(Boolean)
}

const previewList = computed(() => generatePreviewList())

// ==================== 图片加载失败处理 ====================
const handleError = (e: Event) => {
  const img = e.target as HTMLImageElement
  if (img && img.src) {
    // 图片加载失败时的处理逻辑
  }
}

// ==================== 计算上传组件是否显示 ====================
const showUploader = computed(() => {
  return !disabled.value && (!imageDisplayData.value || imageDisplayData.value.length < limit.value)
})

// ==================== 合并请求头 ====================
const uploadHeaders = computed(() => {
  return {
    Authorization: token.value,
    ...props.headers
  }
})

// ==================== 上传文件 ====================
/**
 * 上传文件到服务器
 * @param fileForm FormData 对象，包含文件和额外数据
 * @returns 上传结果
 */
const uploadFile = async (
  fileForm: FormData
): Promise<{ success: boolean; message: string; data?: any }> => {
  try {
    const res = await fetch(props.action, {
      method: 'POST',
      body: fileForm,
      headers: {
        Authorization: token.value || '',
        ...props.headers
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

// ==================== 上传待上传的图片 ====================
/**
 * 上传待上传的图片
 * 检查图片数据中是否有数组格式的项（未上传的图片），如果有则上传
 * 上传成功后，将返回的图片地址转为指定格式后更新图片列表
 *
 * @returns Promise<void> 如果上传失败会抛出错误
 * @throws {Error} 上传失败时抛出错误
 */
const uploadPendingImages = async (): Promise<void> => {
  if (!imageData.value || !Array.isArray(imageData.value)) {
    return
  }

  const newImageData = [...imageData.value]

  for (let index = 0; index < newImageData.length; index++) {
    const fileData = newImageData[index]

    // 如果是数组格式（包含文件对象），说明是未上传的图片，需要上传
    if (Array.isArray(fileData) && fileData.length >= 4) {
      const fileForm = new FormData()
      fileForm.append('file', fileData[3].raw)

      // 添加额外数据
      Object.keys(props.data).forEach((key) => {
        fileForm.append(key, props.data[key])
      })

      const res = await uploadFile(fileForm)
      if (!res.success) {
        throw new Error(`图片上传错误：${res.message}`)
      }

      // 转换为字符串格式：路径 + 操作类型（add/update/delete）
      const operationType = fileData[1] || 'add'
      const remotePath = res.data.data.remote_path
      newImageData[index] = `${remotePath}?${operationType}`
    }
  }

  // 更新数据
  isInternalUpdate.value = true
  imageData.value = newImageData
  // 自动更新显示数据
  imageDisplayData.value = generateDisplayData(newImageData)
}

// ==================== 暴露方法 ====================
defineExpose({
  uploadPendingImages
})
</script>

<template>
  <div class="image-container">
    <template v-for="(image, index) in imageDisplayData" :key="`${index}-${image}`">
      <div
        v-if="image && !image.endsWith('?delete')"
        :class="[
          'image-group',
          !disabled && dragIndex === index ? 'dragging' : '',
          !disabled && dragOverIndex === index ? 'drag-over' : ''
        ]"
        @click.stop
        :draggable="!disabled"
        @dragstart="handleDragStart(index, $event)"
        @dragover="handleDragOver"
        @dragenter="handleDragEnter(index, $event)"
        @dragleave="handleDragLeave"
        @drop="handleDrop(index, $event)"
        @dragend="handleDragEnd"
      >
        <ElImage
          :src="image"
          class="image-item"
          @error="handleError"
          :zoom-rate="1.2"
          :preview-src-list="previewList.length > 0 ? previewList : []"
          preview-teleported
          hide-on-click-modal
          :initial-index="index"
          fit="cover"
          style="width: 100%; height: 100%"
        />
        <div v-if="!disabled" @click.stop="handleRemoveImage(index)" class="remove-btn"> x </div>
      </div>
    </template>
    <div v-if="showUploader" class="image-group-uploader">
      <ElUpload
        :action="action.value"
        :data="data.value"
        :show-file-list="false"
        :multiple="true"
        :auto-upload="false"
        :before-upload="beforeImageUpload"
        @change="handleFileChange"
        accept="image/jpeg,image/gif,image/png"
        name="file"
        drag
        :headers="uploadHeaders"
        :limit="limit.value"
      >
        <div>
          <ElIcon class="el-icon--upload"><UploadFilled /></ElIcon>
          <div class="upload-text">拖拽文件到此或点击上传</div>
        </div>
      </ElUpload>
    </div>
  </div>
</template>

<style lang="less" scoped>
.image-container {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 0;
}

.image-group {
  position: relative;
  width: 100px;
  height: 100px;
  margin: 0;
}

.image-item {
  width: 100%;
  height: 100%;
  border-radius: 6px;
  border: 1px solid #dcdfe6;
  transition: all 0.3s ease;
  cursor: pointer;
}

.image-item:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

// ElImage 组件样式
.image-group :deep(.el-image) {
  width: 100%;
  height: 100%;
  border-radius: 6px;
}

.image-group :deep(.el-image__inner) {
  border-radius: 6px;
  object-fit: cover;
}

.remove-btn {
  position: absolute;
  top: -6px;
  right: -6px;
  width: 24px;
  height: 24px;
  background: #f56c6c;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 12px;
  font-weight: bold;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.image-group:hover .remove-btn {
  opacity: 1;
}

.image-group.dragging {
  opacity: 0.5;
  border-color: #409eff;
  transform: scale(0.95);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
  cursor: grabbing;
  z-index: 1000;
}

.image-group.drag-over {
  transform: scale(1.15);
  border: 2px solid #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
  transform: scale(1.05);
  z-index: 10;
  transition: all 0.2s ease;
}

.image-group-uploader {
  width: 180px;
  height: 100px;
  flex-shrink: 0;
}

.image-group-uploader :deep(.el-upload) {
  border: 2px dashed #c0c4cc;
  width: 100% !important;
  height: 96px !important;
  margin: 0 !important;
  border-radius: 6px;
}

.image-group-uploader :deep(.el-upload:hover) {
  border-color: #409eff;
  background: #f0f7ff;
  color: #409eff;
}

.image-group-uploader :deep(.el-upload-dragger) {
  width: 100% !important;
  height: 100% !important;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
}

.el-icon--upload {
  width: 54px;
  height: 54px;
  margin-top: 0;
}

.upload-text {
  font-size: 12px;
  margin-top: -20px;
  text-align: center;
}
</style>
