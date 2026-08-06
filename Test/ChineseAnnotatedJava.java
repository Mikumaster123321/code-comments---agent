// -*- coding: utf-8 -*-
/**
 * 学生成绩管理系统
 * 本类提供学生成绩的录入、查询、统计等功能。
 */
public class StudentScoreManager {

    /**
     * 内部类：表示一个学生对象
     * 包含学生的基本信息和各科成绩
     */
    public static class Student {
        private String name;    // 学生姓名
        private int mathScore;  // 数学成绩
        private int engScore;   // 英语成绩

        /**
         * 构造学生对象。
         *
         * @param name    学生姓名
         * @param math    数学成绩（0-100）
         * @param english 英语成绩（0-100）
         */
        public Student(String name, int math, int english) {
            this.name = name;
            this.mathScore = math;
            this.engScore = english;
        }

        /**
         * 获取学生姓名。
         *
         * @return 姓名字符串
         */
        public String getName() {
            return name;  // 返回姓名
        }

        /**
         * 计算学生的总分。
         *
         * @return 数学加英语的总分
         */
        public int getTotalScore() {
            return mathScore + engScore;  // 相加两科成绩
        }
    }

    private java.util.List<Student> students;  // 存储所有学生的列表

    /**
     * 初始化成绩管理系统，创建空的学生列表。
     */
    public StudentScoreManager() {
        this.students = new java.util.ArrayList<>();
    }

    /**
     * 添加一个学生到系统中。
     *
     * @param s 要添加的学生对象，不能为null
     */
    public void addStudent(Student s) {
        if (s != null) {
            students.add(s);  // 添加到列表尾部
        }
    }

    /**
     * 查找指定姓名的学生。
     *
     * @param name 要查找的学生姓名
     * @return 找到的学生对象，如果没找到返回null
     */
    public Student findStudent(String name) {
        for (Student s : students) {
            if (s.getName().equals(name)) {
                return s;  // 找到后立即返回
            }
        }
        return null;  // 遍历完毕未找到
    }

    /**
     * 计算全班的平均总分。
     *
     * @return 平均总分的double值，如果没有学生返回0.0
     */
    public double getClassAverage() {
        if (students.isEmpty()) return 0.0;
        int sum = 0;
        for (Student s : students) {
            sum += s.getTotalScore();  // 累加每个学生的总分
        }
        return (double) sum / students.size();  // 除以学生数量
    }
}
