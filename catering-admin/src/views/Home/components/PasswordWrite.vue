<script setup lang="tsx">
import { Form, FormSchema } from '@/components/Form'
import { useForm } from '@/hooks/web/useForm'
import { reactive, ref } from 'vue'
import { useValidator } from '@/hooks/web/useValidator'
import { useAuthStore } from '@/store/modules/auth'
import { ElMessage } from 'element-plus'
import { postCurrentUserResetPassword } from '@/api/vadmin/system/user'
import { BaseButton } from '@/components/Button'
import { useStorage } from '@/hooks/web/useStorage'

const { required } = useValidator()

const authStore = useAuthStore()
const { removeStorage } = useStorage()

const formSchema = reactive<FormSchema[]>([
  {
    field: 'title',
    colProps: {
      span: 24
    }
  },
  {
    field: 'password',
    label: '新密码',
    component: 'InputPassword',
    colProps: {
      span: 24
    },
    componentProps: {
      style: {
        width: '50%'
      },
      placeholder: '请输入新密码'
    }
  },
  {
    field: 'password_two',
    label: '确认密码',
    component: 'InputPassword',
    colProps: {
      span: 24
    },
    componentProps: {
      style: {
        width: '50%'
      },
      placeholder: '请再次输入新密码'
    }
  },
  {
    field: 'save',
    colProps: {
      span: 24
    },
    formItemProps: {
      slots: {
        default: () => {
          return (
            <>
              <div class="w-[50%]">
                <BaseButton loading={loading.value} type="primary" class="w-[100%]" onClick={save}>
                  保存
                </BaseButton>
              </div>
            </>
          )
        }
      }
    }
  }
])

const rules = {
  password: [
    required(),
    { min: 8, max: 16, message: '长度需为8-16个字符,请重新输入。', trigger: 'blur' }
  ],
  password_two: [
    required(),
    { min: 8, max: 16, message: '长度需为8-16个字符,请重新输入。', trigger: 'blur' }
  ]
}

const { formRegister, formMethods } = useForm()
const { setValues, getFormData, getElFormExpose } = formMethods

setValues(authStore.getUser)

const loading = ref(false)

// 提交
const save = async () => {
  const elForm = await getElFormExpose()
  const valid = await elForm?.validate()
  if (valid) {
    loading.value = true
    const formData = await getFormData()
    try {
      const res = await postCurrentUserResetPassword(formData)
      if (res) {
        elForm?.resetFields()
        
        // 清除"记住我"相关的存储，防止浏览器自动填充旧密码
        removeStorage('remember_user')
        removeStorage('remember_telephone')
        
        authStore.logout()
        ElMessage.warning('请重新登录')
      }
    } finally {
      loading.value = false
    }
  }
}
</script>

<template>
  <Form
    @register="formRegister"
    :schema="formSchema"
    :rules="rules"
    hide-required-asterisk
    class="dark:(border-1 border-[var(--el-border-color)] border-solid)"
  />
</template>
