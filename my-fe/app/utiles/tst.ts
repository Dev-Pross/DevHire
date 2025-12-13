import prisma, {UserOperations} from './database'

async function main() {
  const testUser = {
    id: 'b8d53d72-8c4e-4f70-983c-0d9f3a7f65b9',
    email: 'testuser@example.com',
    name: 'Test User',
    resume_url: null,
    applied_jobs: [],
  }

  try {
    const result = await UserOperations(testUser)
    console.log('Upsert result:', result)
  } catch (error) {
    console.error('Error in UserOperations:', error)
  } finally {
    await prisma.$disconnect()
  }
}

// Run the main function
main()