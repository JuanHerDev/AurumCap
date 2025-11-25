// app/learn/page.tsx
"use client";

import { useState, useEffect } from "react";
import { FaBookOpen, FaPlay, FaCheck, FaLock, FaPlus, FaEdit, FaHome, FaBriefcase, FaCalculator, FaChalkboardTeacher } from "react-icons/fa";
import { useAuth } from "@/features/auth/context/AuthProvider";
import { useRouter } from "next/navigation";

// Interfaces
interface Lesson {
  id: string;
  title: string;
  description: string;
  duration: number; // en horas
  difficulty: "beginner" | "intermediate" | "advanced";
  progress: number; // 0-100
  category: string;
  content?: string;
  video_url?: string;
  resources?: string[];
  is_active: boolean;
  order: number;
}

interface Course {
  id: string;
  title: string;
  description: string;
  lessons: Lesson[];
  category: string;
  total_duration: number;
  enrolled_students: number;
  is_active: boolean;
}

// Service para manejar cursos y lecciones
class CourseService {
  private static STORAGE_KEY = 'aurumcap_courses';
  private static DEFAULT_COURSES: Course[] = [
    {
      id: "1",
      title: "Fundamentos de Inversión",
      description: "Aprende los conceptos básicos para comenzar tu journey en inversiones",
      category: "fundamentos",
      total_duration: 4,
      enrolled_students: 150,
      is_active: true,
      lessons: [
        {
          id: "1-1",
          title: "Introducción al Mercado de Valores",
          description: "Conceptos básicos del mercado bursátil",
          duration: 3,
          difficulty: "beginner",
          progress: 100,
          category: "fundamentos",
          order: 1,
          is_active: true
        },
        {
          id: "1-2",
          title: "Tipos de Activos Financieros",
          description: "Conoce los diferentes instrumentos de inversión",
          duration: 1,
          difficulty: "beginner",
          progress: 75,
          category: "fundamentos",
          order: 2,
          is_active: true
        }
      ]
    },
    {
      id: "2",
      title: "Análisis Técnico",
      description: "Técnicas para análisis de gráficos y tendencias",
      category: "analisis",
      total_duration: 6,
      enrolled_students: 89,
      is_active: true,
      lessons: [
        {
          id: "2-1",
          title: "Técnicas para Inversiones",
          description: "Métodos fundamentales de análisis técnico",
          duration: 0,
          difficulty: "intermediate",
          progress: 50,
          category: "analisis",
          order: 1,
          is_active: true
        },
        {
          id: "2-2",
          title: "Patrones de Gráficos",
          description: "Identificación de patrones de continuación y reversión",
          duration: 2,
          difficulty: "intermediate",
          progress: 25,
          category: "analisis",
          order: 2,
          is_active: true
        }
      ]
    },
    {
      id: "3",
      title: "Estrategias Avanzadas de Portafolio",
      description: "Gestión profesional de carteras de inversión",
      category: "avanzado",
      total_duration: 8,
      enrolled_students: 45,
      is_active: true,
      lessons: [
        {
          id: "3-1",
          title: "Optimización de Portafolio",
          description: "Técnicas modernas de optimización",
          duration: 0,
          difficulty: "advanced",
          progress: 0,
          category: "avanzado",
          order: 1,
          is_active: true
        },
        {
          id: "3-2",
          title: "Gestión de Riesgos y Diversificación",
          description: "Estrategias avanzadas de gestión de riesgo",
          duration: 5,
          difficulty: "intermediate",
          progress: 50,
          category: "avanzado",
          order: 2,
          is_active: true
        }
      ]
    }
  ];

  static getCourses(): Course[] {
    if (typeof window === 'undefined') return this.DEFAULT_COURSES;
    
    try {
      const stored = localStorage.getItem(this.STORAGE_KEY);
      return stored ? JSON.parse(stored) : this.DEFAULT_COURSES;
    } catch {
      return this.DEFAULT_COURSES;
    }
  }

  static saveCourses(courses: Course[]) {
    if (typeof window !== 'undefined') {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(courses));
    }
  }

  static addCourse(course: Course) {
    const courses = this.getCourses();
    courses.push(course);
    this.saveCourses(courses);
    return courses;
  }

  static updateCourse(updatedCourse: Course) {
    const courses = this.getCourses();
    const index = courses.findIndex(c => c.id === updatedCourse.id);
    if (index !== -1) {
      courses[index] = updatedCourse;
      this.saveCourses(courses);
    }
    return courses;
  }

  static addLesson(courseId: string, lesson: Lesson) {
    const courses = this.getCourses();
    const courseIndex = courses.findIndex(c => c.id === courseId);
    if (courseIndex !== -1) {
      courses[courseIndex].lessons.push(lesson);
      this.saveCourses(courses);
    }
    return courses;
  }

  static updateLesson(courseId: string, updatedLesson: Lesson) {
    const courses = this.getCourses();
    const courseIndex = courses.findIndex(c => c.id === courseId);
    if (courseIndex !== -1) {
      const lessonIndex = courses[courseIndex].lessons.findIndex(l => l.id === updatedLesson.id);
      if (lessonIndex !== -1) {
        courses[courseIndex].lessons[lessonIndex] = updatedLesson;
        this.saveCourses(courses);
      }
    }
    return courses;
  }
}

export default function LearnPage() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [selectedCourse, setSelectedCourse] = useState<Course | null>(null);
  const [showCourseForm, setShowCourseForm] = useState(false);
  const [showLessonForm, setShowLessonForm] = useState(false);
  const [editingCourse, setEditingCourse] = useState<Course | null>(null);
  const [editingLesson, setEditingLesson] = useState<{ course: Course; lesson: Lesson } | null>(null);
  const { user } = useAuth();
  const router = useRouter();

  const isSupport = user?.role === 'support' || user?.role === 'admin';

  useEffect(() => {
    loadCourses();
  }, []);

  const loadCourses = () => {
    const loadedCourses = CourseService.getCourses();
    setCourses(loadedCourses);
  };

  const handleCourseSelect = (course: Course) => {
    setSelectedCourse(course);
  };

  const handleBackToCourses = () => {
    setSelectedCourse(null);
  };

  const handleAddCourse = (courseData: any) => {
    const newCourse: Course = {
      id: Date.now().toString(),
      title: courseData.title,
      description: courseData.description,
      category: courseData.category,
      total_duration: 0,
      enrolled_students: 0,
      is_active: true,
      lessons: []
    };

    const updatedCourses = CourseService.addCourse(newCourse);
    setCourses(updatedCourses);
    setShowCourseForm(false);
  };

  const handleEditCourse = (courseData: any) => {
    if (!editingCourse) return;

    const updatedCourse: Course = {
      ...editingCourse,
      title: courseData.title,
      description: courseData.description,
      category: courseData.category
    };

    const updatedCourses = CourseService.updateCourse(updatedCourse);
    setCourses(updatedCourses);
    setShowCourseForm(false);
    setEditingCourse(null);
  };

  const handleAddLesson = (lessonData: any) => {
    if (!selectedCourse) return;

    const newLesson: Lesson = {
      id: `${selectedCourse.id}-${Date.now()}`,
      title: lessonData.title,
      description: lessonData.description,
      duration: parseFloat(lessonData.duration) || 0,
      difficulty: lessonData.difficulty,
      progress: 0,
      category: selectedCourse.category,
      order: selectedCourse.lessons.length + 1,
      is_active: true
    };

    const updatedCourses = CourseService.addLesson(selectedCourse.id, newLesson);
    setCourses(updatedCourses);
    setSelectedCourse(updatedCourses.find(c => c.id === selectedCourse.id) || null);
    setShowLessonForm(false);
  };

  const handleEditLesson = (lessonData: any) => {
    if (!editingLesson) return;

    const updatedLesson: Lesson = {
      ...editingLesson.lesson,
      title: lessonData.title,
      description: lessonData.description,
      duration: parseFloat(lessonData.duration) || 0,
      difficulty: lessonData.difficulty
    };

    const updatedCourses = CourseService.updateLesson(editingLesson.course.id, updatedLesson);
    setCourses(updatedCourses);
    setSelectedCourse(updatedCourses.find(c => c.id === editingLesson.course.id) || null);
    setShowLessonForm(false);
    setEditingLesson(null);
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case "beginner": return "bg-green-100 text-green-800";
      case "intermediate": return "bg-yellow-100 text-yellow-800";
      case "advanced": return "bg-red-100 text-red-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  const getDifficultyText = (difficulty: string) => {
    switch (difficulty) {
      case "beginner": return "Principiante";
      case "intermediate": return "Intermedio";
      case "advanced": return "Avanzado";
      default: return difficulty;
    }
  };

  if (selectedCourse) {
    return (
      <CourseDetailView
        course={selectedCourse}
        onBack={handleBackToCourses}
        isSupport={isSupport}
        onEditLesson={(course, lesson) => {
          setEditingLesson({ course, lesson });
          setShowLessonForm(true);
        }}
        onAddLesson={() => setShowLessonForm(true)}
      />
    );
  }

  return (
    <main className="min-h-screen bg-gray-50 text-gray-900 pb-20">
      {/* Header */}
      <header className="bg-white px-4 py-4 border-b border-gray-200 sticky top-0 z-10">
        <div className="flex justify-between items-center max-w-6xl mx-auto">
          <h1 className="text-xl font-bold">
            Centro de <span className="text-[#B59F50]">Aprendizaje</span>
          </h1>
          <div className="flex items-center gap-2 text-xs text-gray-600">
            <FaBookOpen className="text-[#B59F50]" size={16} />
            <span className="hidden xs:inline">Aprender</span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="p-4 max-w-6xl mx-auto">
        {/* Header Section */}
        <section className="mb-6">
          <h2 className="text-lg font-semibold mb-2">Desarrolla tus habilidades de inversión</h2>
          <p className="text-gray-600 text-sm">
            Cursos diseñados para todos los niveles, desde principiantes hasta inversores avanzados.
          </p>
        </section>

        {/* Admin Actions */}
        {isSupport && (
          <section className="mb-6">
            <button
              onClick={() => {
                setEditingCourse(null);
                setShowCourseForm(true);
              }}
              className="w-full bg-[#B59F50] text-white font-semibold py-3 rounded-lg hover:bg-[#A68F45] transition-colors flex items-center justify-center gap-2"
            >
              <FaPlus size={16} />
              Crear Nuevo Curso
            </button>
          </section>
        )}

        {/* Courses Grid */}
        <section className="space-y-4">
          {courses.filter(course => course.is_active).map((course) => (
            <CourseCard
              key={course.id}
              course={course}
              onSelect={handleCourseSelect}
              isSupport={isSupport}
              onEdit={() => {
                setEditingCourse(course);
                setShowCourseForm(true);
              }}
            />
          ))}
        </section>

        {/* Empty State */}
        {courses.length === 0 && (
          <section className="text-center py-12">
            <FaBookOpen className="mx-auto text-gray-400 mb-4" size={48} />
            <h3 className="text-lg font-semibold text-gray-600 mb-2">No hay cursos disponibles</h3>
            <p className="text-gray-500 text-sm">
              {isSupport 
                ? "Comienza creando el primer curso para tus estudiantes."
                : "Próximamente tendremos nuevos cursos disponibles."
              }
            </p>
          </section>
        )}
      </div>

      {/* Forms */}
      {showCourseForm && (
        <CourseForm
          course={editingCourse}
          onSave={editingCourse ? handleEditCourse : handleAddCourse}
          onClose={() => {
            setShowCourseForm(false);
            setEditingCourse(null);
          }}
        />
      )}

      {showLessonForm && (
        <LessonForm
          lesson={editingLesson?.lesson || null}
          onSave={editingLesson ? handleEditLesson : handleAddLesson}
          onClose={() => {
            setShowLessonForm(false);
            setEditingLesson(null);
          }}
        />
      )}

      
    </main>
  );
}

// Componente para tarjeta de curso
function CourseCard({ 
  course, 
  onSelect, 
  isSupport, 
  onEdit 
}: { 
  course: Course; 
  onSelect: (course: Course) => void;
  isSupport: boolean;
  onEdit: () => void;
}) {
  const totalProgress = course.lessons.length > 0 
    ? course.lessons.reduce((sum, lesson) => sum + lesson.progress, 0) / course.lessons.length 
    : 0;

  return (
    <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
      <div className="flex justify-between items-start mb-3">
        <div className="flex-1">
          <h3 className="font-semibold text-gray-900 mb-1">{course.title}</h3>
          <p className="text-gray-600 text-sm mb-2">{course.description}</p>
        </div>
        {isSupport && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onEdit();
            }}
            className="ml-2 p-2 text-gray-400 hover:text-[#B59F50] transition-colors"
          >
            <FaEdit size={14} />
          </button>
        )}
      </div>

      <div className="flex items-center justify-between text-xs text-gray-500 mb-3">
        <span>{course.lessons.length} lecciones • {course.total_duration}h</span>
        <span>{course.enrolled_students} estudiantes</span>
      </div>

      {/* Progress Bar */}
      <div className="mb-3">
        <div className="flex justify-between text-xs text-gray-600 mb-1">
          <span>Progreso</span>
          <span>{Math.round(totalProgress)}% Completado</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className="bg-[#B59F50] h-2 rounded-full transition-all duration-300"
            style={{ width: `${totalProgress}%` }}
          />
        </div>
      </div>

      <button
        onClick={() => onSelect(course)}
        className="w-full bg-[#B59F50] text-white font-semibold py-2 rounded-lg hover:bg-[#A68F45] transition-colors flex items-center justify-center gap-2"
      >
        <FaPlay size={12} />
        {totalProgress > 0 ? 'Continuar' : 'Comenzar'}
      </button>
    </div>
  );
}

// Vista detallada del curso
function CourseDetailView({ 
  course, 
  onBack, 
  isSupport, 
  onEditLesson, 
  onAddLesson 
}: { 
  course: Course;
  onBack: () => void;
  isSupport: boolean;
  onEditLesson: (course: Course, lesson: Lesson) => void;
  onAddLesson: () => void;
}) {
  return (
    <main className="min-h-screen bg-gray-50 text-gray-900 pb-20">
      {/* Header */}
      <header className="bg-white px-4 py-4 border-b border-gray-200 sticky top-0 z-10">
        <div className="flex items-center gap-3 max-w-6xl mx-auto">
          <button
            onClick={onBack}
            className="text-gray-600 hover:text-gray-800 transition-colors"
          >
            ←
          </button>
          <div className="flex-1">
            <h1 className="text-lg font-bold">{course.title}</h1>
            <p className="text-gray-600 text-sm">{course.description}</p>
          </div>
        </div>
      </header>

      <div className="p-4 max-w-6xl mx-auto">
        {/* Admin Actions */}
        {isSupport && (
          <section className="mb-6">
            <button
              onClick={onAddLesson}
              className="w-full bg-green-600 text-white font-semibold py-3 rounded-lg hover:bg-green-700 transition-colors flex items-center justify-center gap-2"
            >
              <FaPlus size={16} />
              Agregar Nueva Lección
            </button>
          </section>
        )}

        {/* Lessons List */}
        <section className="space-y-3">
          {course.lessons
            .filter(lesson => lesson.is_active)
            .sort((a, b) => a.order - b.order)
            .map((lesson) => (
            <LessonCard
              key={lesson.id}
              lesson={lesson}
              isSupport={isSupport}
              onEdit={() => onEditLesson(course, lesson)}
            />
          ))}
        </section>

        {/* Empty Lessons State */}
        {course.lessons.length === 0 && (
          <section className="text-center py-12">
            <FaLock className="mx-auto text-gray-400 mb-4" size={48} />
            <h3 className="text-lg font-semibold text-gray-600 mb-2">No hay lecciones disponibles</h3>
            <p className="text-gray-500 text-sm">
              {isSupport 
                ? "Agrega la primera lección a este curso."
                : "Las lecciones estarán disponibles pronto."
              }
            </p>
          </section>
        )}
      </div>
    </main>
  );
}

// Componente para tarjeta de lección
function LessonCard({ 
  lesson, 
  isSupport, 
  onEdit 
}: { 
  lesson: Lesson; 
  isSupport: boolean;
  onEdit: () => void;
}) {
    function getDifficultyColor(difficulty: string) {
        throw new Error("Function not implemented.");
    }

    function getDifficultyText(difficulty: string): import("react").ReactNode {
        throw new Error("Function not implemented.");
    }

  return (
    <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
      <div className="flex justify-between items-start mb-3">
        <div className="flex-1">
          <h3 className="font-semibold text-gray-900 mb-1">{lesson.title}</h3>
          <p className="text-gray-600 text-sm mb-2">{lesson.description}</p>
        </div>
        {isSupport && (
          <button
            onClick={onEdit}
            className="ml-2 p-2 text-gray-400 hover:text-[#B59F50] transition-colors"
          >
            <FaEdit size={14} />
          </button>
        )}
      </div>

      <div className="flex items-center justify-between text-xs text-gray-500 mb-3">
        <span>{lesson.duration}h</span>
        <span className={`px-2 py-1 rounded-full ${getDifficultyColor(lesson.difficulty)}`}>
          {getDifficultyText(lesson.difficulty)}
        </span>
      </div>

      {/* Progress Bar */}
      <div className="mb-3">
        <div className="flex justify-between text-xs text-gray-600 mb-1">
          <span>Progreso</span>
          <span>{lesson.progress}% Completado</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className="bg-[#B59F50] h-2 rounded-full transition-all duration-300"
            style={{ width: `${lesson.progress}%` }}
          />
        </div>
      </div>

      <button
        onClick={() => {
          // Aquí iría la lógica para comenzar la lección
          console.log('Comenzando lección:', lesson.id);
        }}
        disabled={lesson.progress === 100}
        className={`w-full font-semibold py-2 rounded-lg transition-colors flex items-center justify-center gap-2 ${
          lesson.progress === 100
            ? 'bg-green-600 text-white hover:bg-green-700'
            : 'bg-[#B59F50] text-white hover:bg-[#A68F45]'
        }`}
      >
        {lesson.progress === 100 ? (
          <>
            <FaCheck size={12} />
            Completado
          </>
        ) : (
          <>
            <FaPlay size={12} />
            {lesson.progress > 0 ? 'Continuar' : 'Comenzar'}
          </>
        )}
      </button>
    </div>
  );
}

// Formulario para cursos (simplificado para el ejemplo)
function CourseForm({ course, onSave, onClose }: { course: Course | null; onSave: (data: any) => void; onClose: () => void }) {
  const [formData, setFormData] = useState({
    title: course?.title || '',
    description: course?.description || '',
    category: course?.category || 'fundamentos'
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50">
      <div className="bg-white rounded-xl p-6 w-full max-w-md">
        <h2 className="text-lg font-semibold mb-4">
          {course ? 'Editar Curso' : 'Nuevo Curso'}
        </h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Título del Curso
            </label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({...formData, title: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#B59F50] focus:border-transparent"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Descripción
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              rows={3}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#B59F50] focus:border-transparent resize-none"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Categoría
            </label>
            <select
              value={formData.category}
              onChange={(e) => setFormData({...formData, category: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#B59F50] focus:border-transparent"
            >
              <option value="fundamentos">Fundamentos</option>
              <option value="analisis">Análisis</option>
              <option value="avanzado">Avanzado</option>
              <option value="estrategias">Estrategias</option>
            </select>
          </div>
          <div className="flex gap-3 justify-end">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-[#B59F50] text-white font-semibold rounded-lg hover:bg-[#A68F45] transition-colors"
            >
              {course ? 'Actualizar' : 'Crear'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// Formulario para lecciones (simplificado)
function LessonForm({ lesson, onSave, onClose }: { lesson: Lesson | null; onSave: (data: any) => void; onClose: () => void }) {
  const [formData, setFormData] = useState({
    title: lesson?.title || '',
    description: lesson?.description || '',
    duration: lesson?.duration || 0,
    difficulty: lesson?.difficulty || 'beginner'
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50">
      <div className="bg-white rounded-xl p-6 w-full max-w-md">
        <h2 className="text-lg font-semibold mb-4">
          {lesson ? 'Editar Lección' : 'Nueva Lección'}
        </h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Título de la Lección
            </label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({...formData, title: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#B59F50] focus:border-transparent"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Descripción
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              rows={2}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#B59F50] focus:border-transparent resize-none"
              required
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Duración (horas)
              </label>
              <input
                type="number"
                step="0.5"
                value={formData.duration}
                onChange={(e) => setFormData({...formData, duration: parseFloat(e.target.value) || 0})}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#B59F50] focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Dificultad
              </label>
              <select
                value={formData.difficulty}
                onChange={(e) => setFormData({...formData, difficulty: e.target.value as any})}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#B59F50] focus:border-transparent"
              >
                <option value="beginner">Principiante</option>
                <option value="intermediate">Intermedio</option>
                <option value="advanced">Avanzado</option>
              </select>
            </div>
          </div>
          <div className="flex gap-3 justify-end">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-[#B59F50] text-white font-semibold rounded-lg hover:bg-[#A68F45] transition-colors"
            >
              {lesson ? 'Actualizar' : 'Crear'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// Componente de navegación
function NavItem({ 
  icon, 
  label, 
  href, 
  active = false 
}: { 
  icon: React.ReactNode; 
  label: string; 
  href?: string;
  active?: boolean;
}) {
  const router = useRouter();

  const handleClick = () => {
    if (href) router.push(href);
  };

  return (
    <button
      onClick={handleClick}
      className={`flex flex-col items-center gap-1 px-2 py-1 rounded-lg transition-all duration-200 min-w-[50px] ${
        active 
          ? 'text-[#B59F50] bg-[#B59F50] bg-opacity-10' 
          : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
      }`}
    >
      {icon}
      <span className="text-xs font-medium">{label}</span>
    </button>
  );
}