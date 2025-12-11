<script setup lang="tsx">
import { reactive, ref, watch } from 'vue'
import { Form } from '@/components/Form'
import { useI18n } from '@/hooks/web/useI18n'
import { ElCheckbox, ElLink } from 'element-plus'
import { useForm } from '@/hooks/web/useForm'
import { getRoleMenusApi } from '@/api/login'
import { useAuthStore } from '@/store/modules/auth'
import { usePermissionStore } from '@/store/modules/permission'
import { useRouter } from 'vue-router'
import type { RouteLocationNormalizedLoaded, RouteRecordRaw } from 'vue-router'
import { UserLoginType } from '@/api/login/types'
import { useValidator } from '@/hooks/web/useValidator'
import { FormSchema } from '@/components/Form'
import { BaseButton } from '@/components/Button'
import { useStorage } from '@/hooks/web/useStorage'

const emit = defineEmits(['to-telephone'])

const { required } = useValidator()

const permissionStore = usePermissionStore()

const authStore = useAuthStore()

const { currentRoute, addRoute, push } = useRouter()

const { t } = useI18n()

const { setStorage, getStorage, removeStorage } = useStorage()

const REMEMBER_USER_KEY = 'remember_user'
const REMEMBER_TELEPHONE_KEY = 'remember_telephone'

// 读取保存的用户名和"记住我"状态
const savedRemember = getStorage(REMEMBER_USER_KEY)
const savedTelephone = (getStorage(REMEMBER_TELEPHONE_KEY) as string) || ''
const remember = ref(!!savedRemember)

const rules = {
  telephone: [required()],
  method: [required()],
  password: [required()]
}

const schema = reactive<FormSchema[]>([
  {
    field: 'title',
    colProps: {
      span: 24
    },
    formItemProps: {
      slots: {
        default: () => {
          return <h2 class="text-2xl font-bold text-center w-[100%]">{t('login.login')}</h2>
        }
      }
    }
  },
  {
    field: 'telephone',
    label: t('login.telephone'),
    value: savedTelephone,
    component: 'Input',
    colProps: {
      span: 24
    },
    componentProps: {
      style: {
        width: '100%'
      },
      placeholder: t('login.telephonePlaceholder'),
      maxlength: 11
    }
  },
  {
    field: 'password',
    label: t('login.password'),
    value: '',
    component: 'InputPassword',
    colProps: {
      span: 24
    },
    componentProps: {
      style: {
        width: '100%'
      },
      placeholder: t('login.passwordPlaceholder'),
      autocomplete: 'off'
    }
  },
  {
    field: 'method',
    label: '登录类型',
    value: '0',
    component: 'Input',
    hidden: true
  },
  {
    field: 'tool',
    colProps: {
      span: 24
    },
    formItemProps: {
      slots: {
        default: () => {
          return (
            <>
              <div class="flex justify-between items-center w-[100%]">
                <ElCheckbox v-model={remember.value} label={t('login.remember')} size="small" />
                <ElLink type="primary" underline={false}>
                  {t('login.forgetPassword')}
                </ElLink>
              </div>
            </>
          )
        }
      }
    }
  },
  {
    field: 'login',
    colProps: {
      span: 24
    },
    formItemProps: {
      slots: {
        default: () => {
          return (
            <>
              <div class="w-[100%]">
                <BaseButton
                  loading={loading.value}
                  type="primary"
                  class="w-[100%]"
                  onClick={signIn}
                >
                  {t('login.login')}
                </BaseButton>
              </div>
              <div class="w-[100%] mt-15px">
                <BaseButton class="w-[100%]" onClick={toTelephoneLogin}>
                  {t('login.smsLogin')}
                </BaseButton>
              </div>
            </>
          )
        }
      }
    }
  }
])

const { formRegister, formMethods } = useForm()
const { getFormData, getElFormExpose } = formMethods
const loading = ref(false)
const redirect = ref<string>('')

watch(
  () => currentRoute.value,
  (route: RouteLocationNormalizedLoaded) => {
    redirect.value = route?.query?.redirect as string
  },
  {
    immediate: true
  }
)

// 登录
const signIn = async () => {
  const elForm = await getElFormExpose()
  const valid = await elForm?.validate()
  if (valid) {
    loading.value = true
    const formData: UserLoginType = await getFormData()
    try {
      const res = await authStore.login(formData)
      if (res) {
        // 处理"记住我"功能
        if (remember.value) {
          // 保存用户名和记住我状态
          setStorage(REMEMBER_TELEPHONE_KEY, formData.telephone)
          setStorage(REMEMBER_USER_KEY, true)
        } else {
          // 清除保存的用户名
          removeStorage(REMEMBER_TELEPHONE_KEY)
          removeStorage(REMEMBER_USER_KEY)
        }
        
        if (!res.data.is_reset_password) {
          // 重置密码
          push({ path: '/reset/password' })
        } else {
          // 获取动态路由
          getMenu()
        }
      } else {
        loading.value = false
      }
    } catch (e: any) {
      loading.value = false
    }
  }
}

// 获取用户菜单信息
const getMenu = async () => {
  const res = await getRoleMenusApi()
  if (res) {
    const routers = res.data || []
    await permissionStore.generateRoutes(routers).catch(() => {})
    permissionStore.getAddRouters.forEach((route) => {
      addRoute(route as RouteRecordRaw) // 动态添加可访问路由表
    })
    permissionStore.setIsAddRouters(true)
    push({ path: redirect.value || permissionStore.addRouters[0].path })
  }
}

// 手机验证码登录
const toTelephoneLogin = () => {
  emit('to-telephone')
}
</script>

<template>
  <Form
    :schema="schema"
    :rules="rules"
    label-position="top"
    hide-required-asterisk
    size="large"
    class="dark:(border-1 border-[var(--el-border-color)] border-solid)"
    @register="formRegister"
  />
</template>
