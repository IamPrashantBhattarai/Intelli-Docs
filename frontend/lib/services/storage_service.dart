// lib/services/storage_service.dart
import 'dart:io';
import 'package:path_provider/path_provider.dart';
import 'package:path/path.dart' as p;

class StorageService {
  static final StorageService _instance = StorageService._internal();
  factory StorageService() => _instance;
  StorageService._internal();

  Future<Directory> get _appDocumentsDir async =>
      await getApplicationDocumentsDirectory();
  Future<Directory> get _tempDir async => await getTemporaryDirectory();

  Future<String> saveFile({
    required File file,
    required String type,
    bool permanent = true,
  }) async {
    try {
      final Directory targetDir =
          permanent ? await _appDocumentsDir : await _tempDir;
      final String subDir = permanent ? 'persistent/$type' : 'temp/$type';
      final Directory finalDir = Directory(p.join(targetDir.path, subDir));

      if (!await finalDir.exists()) await finalDir.create(recursive: true);

      final String extension = p.extension(file.path);
      final String filename =
          '${DateTime.now().millisecondsSinceEpoch}$extension';
      final String newPath = p.join(finalDir.path, filename);

      return (await file.copy(newPath)).path;
    } catch (e) {
      throw Exception('Failed to save file: $e');
    }
  }

  Future<File> getFile(String path) async {
    final file = File(path);
    if (await file.exists()) return file;
    throw Exception('File not found');
  }

  Future<void> clearTempFiles() async {
    final tempDir = await _tempDir;
    final Directory tempFilesDir = Directory(p.join(tempDir.path, 'temp'));
    if (await tempFilesDir.exists()) await tempFilesDir.delete(recursive: true);
  }

  Future<List<File>> getAllStoredFiles() async {
    final appDir = await _appDocumentsDir;
    final List<File> files = [];
    await for (var file in appDir.list(recursive: true)) {
      if (file is File) files.add(file);
    }
    return files;
  }
}
